#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const skillRoot = path.resolve(import.meta.dirname, "..");
const profileRoot = path.join(skillRoot, "profiles");
const home = os.homedir();
const cwd = process.cwd();
const jsonOutput = process.argv.includes("--json");

function expand(value) {
  return value.replaceAll("${HOME}", home).replaceAll("${CWD}", cwd);
}

function commandExists(command) {
  return spawnSync("sh", ["-lc", `command -v ${command}`], { stdio: "ignore" }).status === 0;
}

function loadProfiles() {
  return fs.readdirSync(profileRoot)
    .filter((file) => file.endsWith(".json"))
    .map((file) => JSON.parse(fs.readFileSync(path.join(profileRoot, file), "utf8")));
}

function countSkills(root, seen = new Set()) {
  if (!fs.existsSync(root)) return 0;
  let real;
  try {
    real = fs.realpathSync(root);
  } catch {
    return 0;
  }
  if (!fs.statSync(real).isDirectory()) return path.basename(root) === "SKILL.md" ? 1 : 0;
  if (seen.has(real)) return 0;
  seen.add(real);
  let count = 0;
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const target = path.join(root, entry.name);
    if (entry.name === "SKILL.md" && entry.isFile()) count += 1;
    else if (entry.isDirectory() || entry.isSymbolicLink()) count += countSkills(target, seen);
  }
  return count;
}

function inspect(profile) {
  const commands = profile.commands.map((command) => ({ command, found: commandExists(command) }));
  const markers = profile.markers.map(expand).map((file) => ({ path: file, found: fs.existsSync(file) }));
  const detected = profile.id === "generic-agent" || commands.some((item) => item.found) || markers.some((item) => item.found);
  if (!detected) return null;
  const skillRoots = profile.skillRoots.map(expand).map((root) => ({
    path: root,
    found: fs.existsSync(root),
    skills: countSkills(root),
  }));
  const rules = profile.rules.map(expand).map((file) => ({ path: file, found: fs.existsSync(file) }));
  return {
    id: profile.id,
    support: profile.support,
    commands,
    markers,
    skillRoots,
    rules,
    explicitInvocation: profile.explicitInvocation,
    adapter: profile.adapter,
  };
}

const clients = loadProfiles().map(inspect).filter(Boolean);
const result = {
  schemaVersion: 1,
  mode: "audit-only",
  cwd,
  clients,
  nextStep: "Read one matching profile and produce a reversible plan before any configuration change.",
};

if (jsonOutput) {
  console.log(JSON.stringify(result, null, 2));
} else {
  console.log(`Detected ${clients.length - 1} known client(s).`);
  for (const client of clients) {
    const total = client.skillRoots.reduce((sum, root) => sum + root.skills, 0);
    console.log(`- ${client.id}: ${client.support}; ${total} discovered Skill file(s)`);
  }
  console.log(result.nextStep);
}
