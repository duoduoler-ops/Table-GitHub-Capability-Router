#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [plugin, skill] = process.argv.slice(2);
if (!plugin || !skill) {
  console.error("Usage: resolve-plugin-skill.mjs <plugin> <skill>");
  process.exit(2);
}

const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
const cacheRoot = path.join(codexHome, "plugins/cache");
const matches = [];
for (const marketplace of fs.existsSync(cacheRoot) ? fs.readdirSync(cacheRoot) : []) {
  const pluginRoot = path.join(cacheRoot, marketplace, plugin);
  if (!fs.existsSync(pluginRoot)) continue;
  for (const version of fs.readdirSync(pluginRoot)) {
    const candidate = path.join(pluginRoot, version, "skills", skill, "SKILL.md");
    if (fs.existsSync(candidate)) matches.push(candidate);
  }
}
matches.sort((left, right) => fs.statSync(right).mtimeMs - fs.statSync(left).mtimeMs);
if (!matches[0]) {
  console.error(`Plugin Skill not found: ${plugin}:${skill}`);
  process.exit(1);
}
console.log(matches[0]);
