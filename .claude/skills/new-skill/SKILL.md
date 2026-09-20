---
name: new-skill
description: Scaffold a new skill or plugin in the agent-skills marketplace repo. Use when the user asks to add, create, or scaffold a skill or plugin in this repository, or asks how this repo is structured.
---

# Add to this marketplace

This repo is a plugin marketplace. `.claude-plugin/marketplace.json` lists the plugins;
each plugin lives in `plugins/<plugin>/` and holds its skills in
`plugins/<plugin>/skills/<skill>/SKILL.md`.

Adding a skill to an existing plugin needs no registration — `skills/` is
auto-discovered. Adding a whole new plugin needs a manifest and a marketplace entry.

## A new skill in an existing plugin

1. Pick a kebab-case name, e.g. `release-notes`.
2. Create the directory and `SKILL.md`:

   ```
   plugins/<plugin>/skills/release-notes/
   ├── SKILL.md
   ├── references/       # optional, read on demand
   └── scripts/          # optional helper scripts
   ```

3. Write the frontmatter. Both fields are required:

   ```yaml
   ---
   name: release-notes
   description: Generate release notes from merged PRs. Use when the user asks for a changelog or release notes for a version or tag.
   ---
   ```

   - `name` must match the directory name and be kebab-case. Always set it
     explicitly — without it the skill falls back to the install directory
     name, which changes on update.
   - `description` is what Claude matches against to decide whether to load the
     skill. Say both *what it does* and *when to use it*, with the concrete words a
     user would type. A vague description means the skill never fires.

4. Write the body as instructions to the agent, not documentation for a human. Keep
   `SKILL.md` short and push detail into `references/` files the agent reads only when
   it needs them.

## A new plugin

1. `plugins/<name>/.claude-plugin/plugin.json` — `name` is the only required field;
   `displayName`, `description`, `version`, `author`, `license` and `keywords` are
   worth setting. Copy `plugins/ticket-review/.claude-plugin/plugin.json`.
2. Put skills in `plugins/<name>/skills/`, slash commands in `plugins/<name>/commands/`.
   Both are auto-discovered.
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json` with `name`
   and `source: "./plugins/<name>"`.
4. Add a row to the plugin table in the root `README.md`.

## Before committing

```bash
claude plugin validate .                    # marketplace manifest
claude plugin validate ./plugins/<name>     # plugin manifest
```

Then install from the local clone and confirm the skill actually triggers on a
realistic prompt:

```
/plugin marketplace add /path/to/agent-skills
/plugin install <name>@agent-skills
```

Run `/plugin marketplace update` after each change.
