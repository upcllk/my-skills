#!/usr/bin/env node

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

const dryRun = process.argv.includes("--dry-run");
const home = homedir();
const sourcePath = join(home, ".mcp", "mysql-servers.json");
// `npx` 首次启动 MySQL MCP 可能超过客户端默认等待时间。
const codexMySqlStartupTimeoutSec = 30;

function fail(message) {
  console.error(`Error: ${message}`);
  process.exit(1);
}

function readJson(path, label) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    fail(`${label} is not valid JSON: ${error.message}`);
  }
}

if (!existsSync(sourcePath)) fail(`Source configuration not found: ${sourcePath}`);
const source = readJson(sourcePath, "Source configuration");
const servers = source.mcpServers;

if (!servers || typeof servers !== "object" || Array.isArray(servers) || Object.keys(servers).length === 0) {
  fail("Source configuration must contain a non-empty mcpServers object.");
}

for (const [name, server] of Object.entries(servers)) {
  if (!/^[A-Za-z0-9_-]+$/.test(name)) fail(`Unsupported MCP server name: ${name}`);
  if (!server || typeof server.command !== "string" || !Array.isArray(server.args) || !server.env || typeof server.env !== "object") {
    fail(`Server ${name} must define command, args, and env.`);
  }
}

function writeJson(path, value) {
  if (!dryRun) writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function syncJsonClient(label, path, extraServerFields = {}, createWhenDirectoryExists = false) {
  if (!existsSync(path) && (!createWhenDirectoryExists || !existsSync(dirname(path)))) {
    return "skipped (configuration not found)";
  }
  const config = existsSync(path) ? readJson(path, label) : {};
  if (config.mcpServers === undefined) config.mcpServers = {};
  if (!config.mcpServers || typeof config.mcpServers !== "object" || Array.isArray(config.mcpServers)) {
    fail(`${label} mcpServers must be an object.`);
  }
  for (const [name, server] of Object.entries(servers)) {
    config.mcpServers[name] = { ...extraServerFields, ...server };
  }
  writeJson(path, config);
  return dryRun ? "would update" : "updated";
}

function tomlString(value) {
  return JSON.stringify(String(value));
}

function removeCodexSections(content) {
  const names = new Set(Object.keys(servers));
  let skipping = false;
  const kept = [];
  for (const line of content.split(/\r?\n/)) {
    if (/^\[[^\]]+\]\s*$/.test(line)) {
      const match = line.match(/^\[mcp_servers\.([^\.\]]+)(?:\.env)?\]\s*$/);
      skipping = Boolean(match && names.has(match[1]));
      if (skipping) continue;
    }
    if (!skipping) kept.push(line);
  }
  return kept
    .join("\n")
    .replace(/\n?# BEGIN shared MySQL MCP[\s\S]*?# END shared MySQL MCP\n?/g, "\n")
    .replace(/\n{3,}/g, "\n")
    .trimEnd();
}

function renderCodexSections() {
  const lines = ["# BEGIN shared MySQL MCP"];
  for (const [name, server] of Object.entries(servers)) {
    lines.push(`\n[mcp_servers.${name}]`);
    lines.push(`command = ${tomlString(server.command)}`);
    lines.push(`args = [${server.args.map(tomlString).join(", ")}]`);
    lines.push(`startup_timeout_sec = ${codexMySqlStartupTimeoutSec}`);
    lines.push(`\n[mcp_servers.${name}.env]`);
    for (const [key, value] of Object.entries(server.env)) lines.push(`${key} = ${tomlString(value)}`);
  }
  lines.push("# END shared MySQL MCP");
  return lines.join("\n");
}

function syncCodex() {
  const path = join(home, ".codex", "config.toml");
  if (!existsSync(path)) return "skipped (configuration not found)";
  const existing = readFileSync(path, "utf8");
  const updated = `${removeCodexSections(existing)}\n\n${renderCodexSections()}\n`;
  if (!dryRun) writeFileSync(path, updated, "utf8");
  return dryRun ? "would update" : "updated";
}

const codex = syncCodex();
const copilot = syncJsonClient("Copilot configuration", join(home, ".copilot", "mcp-config.json"), {
  tools: ["*"],
  type: "stdio",
});
const claude = syncJsonClient(
  "Claude Desktop configuration",
  join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json"),
  {},
  true,
);

console.log(`Codex: ${codex}`);
console.log(`Copilot: ${copilot}`);
console.log(`Claude Desktop: ${claude}`);
