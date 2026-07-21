#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
const mode = process.argv.find((item) => item.startsWith("--")) ?? "--check";
const skillRoot = path.resolve(import.meta.dirname, "..");
const home = os.homedir();
const codexHome = process.env.CODEX_HOME || path.join(home, ".codex");
const stateRoot = path.join(codexHome, "capability-optimizer");
const wrapperRoot = path.join(stateRoot, "plugin-wrappers");
const manifestPath = path.join(stateRoot, "plugin-skill-wrappers.json");
const indexPath = path.join(stateRoot, "capability-index.json");
const configPath = path.join(codexHome, "config.toml");
const agentsSkillRoot = path.join(home, ".agents/skills");
const cacheRoot = path.join(codexHome, "plugins/cache");
const markerStart = "# BEGIN CAPABILITY OPTIMIZER EXPLICIT PLUGIN SKILLS";
const markerEnd = "# END CAPABILITY OPTIMIZER EXPLICIT PLUGIN SKILLS";
const legacyMarkers = [["# BEGIN THIRDSPACE EXPLICIT PLUGIN SKILLS", "# END THIRDSPACE EXPLICIT PLUGIN SKILLS"]];
const lockPath = path.join(os.tmpdir(), "codex-capability-optimizer.lock");
function timestamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/T/, "-").slice(0, 15);
}
function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return fallback;
  }
}
function codexBinary() {
  const bundled = "/Applications/ChatGPT.app/Contents/Resources/codex";
  return fs.existsSync(bundled) ? bundled : "codex";
}
function visibleSkills() {
  const result = spawnSync(codexBinary(), ["debug", "prompt-input", "capability audit"], {
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
  });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout);
  const messages = JSON.parse(result.stdout);
  const text = messages
    .flatMap((message) => message.content ?? [])
    .map((content) => content.text ?? "")
    .join("\n");
  const block = text.match(/<skills_instructions>([\s\S]*?)<\/skills_instructions>/)?.[1] ?? "";
  return [...block.matchAll(/^- ([^:]+(?::[^:]+)?): (.*?) \(file: ([^)]+)\)$/gm)].map(
    ([, name, description, file]) => ({ name, description, file }),
  );
}
function pluginIdentity(file) {
  const relative = path.relative(cacheRoot, file);
  if (relative.startsWith("..")) return null;
  const parts = relative.split(path.sep);
  if (parts.length !== 6 || parts[3] !== "skills" || parts[5] !== "SKILL.md") return null;
  return { marketplace: parts[0], plugin: parts[1], version: parts[2], skill: parts[4] };
}
function managedPluginEntries(config) {
  const blocks = [[markerStart, markerEnd], ...legacyMarkers].flatMap(([startMarker, endMarker]) => {
    const start = config.indexOf(startMarker);
    if (start === -1) return [];
    const end = config.indexOf(endMarker, start);
    if (end === -1) throw new Error("Managed Plugin Skill block has no end marker");
    return [config.slice(start, end)];
  }).join("\n");
  return [...blocks.matchAll(/^path = ["'](.+?)["']$/gm)]
    .map(([, file]) => pluginIdentity(file))
    .filter(Boolean);
}
function latestPluginRoot(plugin) {
  if (!fs.existsSync(cacheRoot)) return null;
  const candidates = [];
  for (const marketplace of fs.readdirSync(cacheRoot)) {
    const pluginRoot = path.join(cacheRoot, marketplace, plugin);
    if (!fs.existsSync(pluginRoot)) continue;
    for (const version of fs.readdirSync(pluginRoot)) {
      const candidate = path.join(pluginRoot, version);
      if (fs.existsSync(path.join(candidate, ".codex-plugin/plugin.json"))) candidates.push(candidate);
    }
  }
  return candidates.sort((left, right) => fs.statSync(right).mtimeMs - fs.statSync(left).mtimeMs)[0] ?? null;
}
function walkSkills(root, seen = new Set()) {
  if (!fs.existsSync(root)) return [];
  let realRoot;
  try {
    realRoot = fs.realpathSync(root);
  } catch {
    return [];
  }
  if (seen.has(realRoot)) return [];
  seen.add(realRoot);
  const results = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (entry.name === ".system" || entry.name.startsWith("plugin-")) continue;
    const target = path.join(root, entry.name);
    if (entry.isDirectory() || entry.isSymbolicLink()) {
      const skill = path.join(target, "SKILL.md");
      if (fs.existsSync(skill)) results.push(skill);
      else results.push(...walkSkills(target, seen));
    }
  }
  return results;
}
function skillMetadata(file) {
  const source = fs.readFileSync(file, "utf8");
  return {
    name: source.match(/^name:\s*["']?([^"'\n]+)["']?$/m)?.[1]?.trim() ?? path.basename(path.dirname(file)),
    description: source.match(/^description:\s*["']?([^"'\n]+)["']?$/m)?.[1]?.trim() ?? "",
    file,
  };
}
function setExplicitOnly(source) {
  const lines = source.replace(/\s+$/, "").split("\n");
  const policy = lines.findIndex((line) => /^policy:\s*$/.test(line));
  if (policy === -1) return `${lines.join("\n")}\n\npolicy:\n  allow_implicit_invocation: false\n`;
  let end = lines.length;
  for (let index = policy + 1; index < lines.length; index += 1) {
    if (/^[^\s#]/.test(lines[index])) {
      end = index;
      break;
    }
  }
  const setting = lines.findIndex(
    (line, index) => index > policy && index < end && /^\s+allow_implicit_invocation:/.test(line),
  );
  if (setting === -1) lines.splice(policy + 1, 0, "  allow_implicit_invocation: false");
  else lines[setting] = "  allow_implicit_invocation: false";
  return `${lines.join("\n")}\n`;
}
function removeManagedBlock(source) {
  return [[markerStart, markerEnd], ...legacyMarkers].reduce(removeBlock, source).trimEnd();
}
function removeBlock(source, [startMarker, endMarker]) {
  const start = source.indexOf(startMarker);
  if (start === -1) return source.trimEnd();
  const end = source.indexOf(endMarker, start);
  if (end === -1) throw new Error("Managed Plugin Skill block has no end marker");
  return `${source.slice(0, start).trimEnd()}\n${source.slice(end + endMarker.length).trimStart()}`.trimEnd();
}
function wrapperContent(entry) {
  const resolver = path.join(skillRoot, "scripts/resolve-plugin-skill.mjs");
  return {
    skill: `---\nname: ${entry.plugin}-${entry.skill}\ndescription: "Explicit wrapper for ${entry.plugin}:${entry.skill}. Loads Plugin instructions only when selected."\n---\n\n# ${entry.plugin}:${entry.skill}\n\n1. Run \`node ${JSON.stringify(resolver)} ${entry.plugin} ${entry.skill}\`.\n2. Read the returned \`SKILL.md\` and follow it as authoritative.\n3. Preserve its confirmation, permission, cleanup, and verification rules.\n`,
    metadata: `interface:\n  display_name: "${entry.plugin}: ${entry.skill}"\n  short_description: "Explicit Plugin Skill"\n\npolicy:\n  allow_implicit_invocation: false\n`,
  };
}
function desiredConfig(config, entries) {
  const rows = entries
    .map((entry) => {
      const target = entry.active ? entry.source : path.join(entry.wrapper, "SKILL.md");
      return `[[skills.config]]\npath = ${JSON.stringify(target)}\nenabled = false`;
    })
    .join("\n\n");
  return `${removeManagedBlock(config)}\n\n${markerStart}\n# Original Plugin Skills are replaced by explicit-only local wrappers.\n\n${rows}\n${markerEnd}\n`;
}
function wrapperPath(plugin, skill) {
  const link = path.join(agentsSkillRoot, `plugin-${plugin}-${skill}`);
  try {
    const current = fs.realpathSync(link);
    if (fs.existsSync(path.join(current, "SKILL.md"))) return current;
  } catch {}
  return path.join(wrapperRoot, `${plugin}-${skill}`);
}
function ensureRouter() {
  const existing = [path.join(codexHome, "skills/capability-router"), path.join(agentsSkillRoot, "capability-router")];
  if (existing.some((item) => fs.existsSync(path.join(item, "SKILL.md")))) return null;
  return {
    target: path.join(codexHome, "skills/capability-router"),
    skillTemplate: path.join(skillRoot, "assets/capability-router/SKILL.template.md"),
    metadataTemplate: path.join(skillRoot, "assets/capability-router/openai.template.yaml"),
  };
}
function verify() {
  const visible = visibleSkills();
  const leaks = visible.filter((item) => pluginIdentity(item.file));
  console.log(JSON.stringify({ visibleSkills: visible.length, pluginLeaks: leaks, names: visible.map((item) => item.name) }, null, 2));
  process.exitCode = leaks.length ? 1 : 0;
}
if (mode === "--verify") {
  verify();
} else {
  let lock;
  try {
    lock = fs.openSync(lockPath, "wx");
  } catch (error) {
    if (error.code === "EEXIST") process.exit(0);
    throw error;
  }
  try {
    const config = fs.readFileSync(configPath, "utf8");
    const visible = visibleSkills();
    const existing = readJson(manifestPath, []);
    const byKey = new Map(existing.map((entry) => [`${entry.plugin}:${entry.skill}`, entry]));
    for (const identity of managedPluginEntries(config)) byKey.set(`${identity.plugin}:${identity.skill}`, identity);
    for (const item of visible) {
      const identity = pluginIdentity(item.file);
      if (identity) byKey.set(`${identity.plugin}:${identity.skill}`, identity);
    }
    const entries = [...byKey.values()]
      .map((entry) => {
        const root = latestPluginRoot(entry.plugin);
        const source = root && path.join(root, "skills", entry.skill, "SKILL.md");
        return {
          plugin: entry.plugin,
          skill: entry.skill,
          source: source && fs.existsSync(source) ? source : entry.source,
          wrapper: wrapperPath(entry.plugin, entry.skill),
          active: Boolean(source && fs.existsSync(source)),
        };
      })
      .sort((left, right) => `${left.plugin}:${left.skill}`.localeCompare(`${right.plugin}:${right.skill}`));
    const personal = [...new Set([
      ...walkSkills(path.join(codexHome, "skills")),
      ...walkSkills(agentsSkillRoot),
    ])].map(skillMetadata).filter((item) => !["capability-router", "optimize-codex-capabilities"].includes(item.name));
    const metadataChanges = personal.flatMap((item) => {
      const file = path.join(path.dirname(item.file), "agents/openai.yaml");
      const source = fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "";
      const desired = setExplicitOnly(source);
      return desired === source ? [] : [{ file, source, desired }];
    });
    const wrapperChanges = entries.flatMap((entry) => {
      if (fs.existsSync(path.join(entry.wrapper, "SKILL.md")) &&
          fs.existsSync(path.join(entry.wrapper, "agents/openai.yaml"))) return [];
      const content = wrapperContent(entry);
      return [
        { file: path.join(entry.wrapper, "SKILL.md"), desired: content.skill },
        { file: path.join(entry.wrapper, "agents/openai.yaml"), desired: content.metadata },
      ].filter((item) => !fs.existsSync(item.file) || fs.readFileSync(item.file, "utf8") !== item.desired);
    });
    const router = ensureRouter();
    const capabilityIndex = `${JSON.stringify({
      personal: personal.map((item) => ({ ...item, type: "personal-skill" })),
      plugins: entries.map((item) => ({ ...item, type: "plugin-wrapper" })),
    }, null, 2)}\n`;
    const manifest = `${JSON.stringify(entries, null, 2)}\n`;
    const nextConfig = desiredConfig(config, entries);
    const currentIndex = fs.existsSync(indexPath) ? fs.readFileSync(indexPath, "utf8") : "";
    const drift = metadataChanges.length + wrapperChanges.length + Number(router !== null) +
      Number(readJson(manifestPath, null) === null || fs.readFileSync(manifestPath, "utf8") !== manifest) +
      Number(currentIndex !== capabilityIndex) + Number(config !== nextConfig);
    const result = {
      mode,
      drift,
      personalSkills: personal.length,
      personalPoliciesToUpdate: metadataChanges.length,
      pluginWrappers: entries.length,
      activePluginWrappers: entries.filter((item) => item.active).length,
      stalePluginWrappers: entries.filter((item) => !item.active).length,
      routerToInstall: Boolean(router),
    };
    if (mode === "--apply" && drift > 0) {
      const backupRoot = path.join(codexHome, "backups", `capability-optimizer-${timestamp()}`);
      fs.mkdirSync(backupRoot, { recursive: true });
      fs.copyFileSync(configPath, path.join(backupRoot, "config.toml"));
      for (const change of metadataChanges) {
        if (change.source) {
          const backup = path.join(backupRoot, "metadata", change.file.replace(/^\//, ""));
          fs.mkdirSync(path.dirname(backup), { recursive: true });
          fs.writeFileSync(backup, change.source);
        }
        fs.mkdirSync(path.dirname(change.file), { recursive: true });
        fs.writeFileSync(change.file, change.desired);
      }
      for (const change of wrapperChanges) {
        fs.mkdirSync(path.dirname(change.file), { recursive: true });
        fs.writeFileSync(change.file, change.desired);
      }
      fs.mkdirSync(agentsSkillRoot, { recursive: true });
      for (const entry of entries) {
        const link = path.join(agentsSkillRoot, `plugin-${entry.plugin}-${entry.skill}`);
        try {
          if (fs.realpathSync(link) === fs.realpathSync(entry.wrapper)) continue;
        } catch {}
        try {
          if (fs.lstatSync(link).isSymbolicLink()) fs.unlinkSync(link);
          else throw new Error(`Unexpected non-symlink: ${link}`);
        } catch (error) {
          if (error.code !== "ENOENT") throw error;
        }
        fs.symlinkSync(entry.wrapper, link, "dir");
      }
      if (router) {
        fs.mkdirSync(path.join(router.target, "agents"), { recursive: true });
        fs.copyFileSync(router.skillTemplate, path.join(router.target, "SKILL.md"));
        fs.copyFileSync(router.metadataTemplate, path.join(router.target, "agents/openai.yaml"));
      }
      fs.mkdirSync(stateRoot, { recursive: true });
      fs.writeFileSync(manifestPath, manifest);
      fs.writeFileSync(indexPath, capabilityIndex);
      fs.writeFileSync(configPath, nextConfig);
      result.backupRoot = backupRoot;
    }
    console.log(JSON.stringify(result, null, 2));
  } finally {
    fs.closeSync(lock);
    fs.unlinkSync(lockPath);
  }
}
