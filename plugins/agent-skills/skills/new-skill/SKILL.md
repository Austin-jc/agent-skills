---
name: new-skill
description: Scaffold a new skill in the agent-skills plugin repo. Use when the user asks to add, create, or scaffold a skill in this repository, or asks how skills in this repo are structured.
---

# Add a skill to this repo

Skills live under `plugins/<plugin>/skills/<skill-name>/SKILL.md`. The default
plugin is `plugins/agent-skills`.

## Steps

1. Pick a kebab-case name, e.g. `release-notes`.
2. Create the directory and `SKILL.md`:

   ```
   plugins/agent-skills/skills/release-notes/
   ├── SKILL.md
   ├── reference.md      # optional, loaded on demand
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
   - `description` is what Claude matches against to decide whether to load
     the skill. Say both *what it does* and *when to use it*, with the concrete
     words a user would type. A vague description means the skill never fires.

4. Write the body as instructions to the agent, not documentation for a human.
   Keep `SKILL.md` short and push detail into sibling files the agent can read
   when it needs them.

5. Nothing needs to be registered: `skills/` is auto-discovered. Only edit
   `.claude-plugin/marketplace.json` when adding a whole new *plugin*.

## Testing before committing

```bash
/plugin marketplace add /home/user/agent-skills   # or the local clone path
/plugin install agent-skills@agent-skills
```

Then start a session and confirm the skill appears and triggers on a realistic
prompt. Run `/plugin marketplace update` after each change.
