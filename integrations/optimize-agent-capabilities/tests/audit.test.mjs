import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

const script = path.resolve(import.meta.dirname, "../scripts/audit.mjs");

test("detects profiles and inventories shared Skill roots without writing", (t) => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "agent-capability-audit-"));
  t.after(() => fs.rmSync(fixture, { recursive: true, force: true }));
  const home = path.join(fixture, "home");
  const cwd = path.join(fixture, "project");
  const bin = path.join(fixture, "bin");
  fs.mkdirSync(path.join(home, ".kimi-code"), { recursive: true });
  fs.mkdirSync(path.join(home, ".codex"), { recursive: true });
  fs.mkdirSync(path.join(home, ".agents/skills/shared"), { recursive: true });
  fs.mkdirSync(path.join(home, ".kimi/skills/native"), { recursive: true });
  fs.mkdirSync(path.join(home, ".agents/skills/shared/.venv/bin"), { recursive: true });
  fs.mkdirSync(cwd, { recursive: true });
  fs.mkdirSync(bin, { recursive: true });
  fs.writeFileSync(path.join(home, ".agents/skills/shared/SKILL.md"), "---\nname: shared\n---\n");
  fs.writeFileSync(path.join(home, ".kimi/skills/native/SKILL.md"), "---\nname: native\n---\n");
  fs.writeFileSync(path.join(fixture, "python"), "binary placeholder");
  const codexCommand = process.platform === "win32" ? "codex.cmd" : "codex";
  fs.writeFileSync(path.join(bin, codexCommand), "read-only command placeholder");
  if (process.platform !== "win32") fs.chmodSync(path.join(bin, codexCommand), 0o755);
  if (process.platform !== "win32") {
    fs.symlinkSync(path.join(fixture, "python"), path.join(home, ".agents/skills/shared/.venv/bin/python"));
  }

  const result = spawnSync(process.execPath, [script, "--json"], {
    cwd,
    encoding: "utf8",
    env: { ...process.env, HOME: home, USERPROFILE: home, PATH: bin },
  });
  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.equal(report.mode, "audit-only");
  assert.ok(report.clients.some((client) => client.id === "kimi-code"));
  assert.ok(report.clients.some((client) => client.id === "generic-agent"));
  const codex = report.clients.find((client) => client.id === "codex");
  assert.equal(codex.support, "audit-only");
  assert.equal(codex.adapter, null);
  assert.equal(codex.commands.find((item) => item.command === "codex").found, true);
  assert.equal(fs.existsSync(path.join(home, ".codex/config.toml")), false);
});
