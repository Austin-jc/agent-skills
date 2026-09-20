# agent-skills

A Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
hosting Austin's agent skills.

## Install

```
/plugin marketplace add austin-jc/agent-skills
/plugin install agent-skills@agent-skills
```

Update later with `/plugin marketplace update`.

To try local changes before pushing, add the clone path instead:

```
/plugin marketplace add ./path/to/agent-skills
```

## Layout

```
.claude-plugin/
└── marketplace.json              # marketplace manifest — lists the plugins below
plugins/
└── agent-skills/
    ├── .claude-plugin/
    │   └── plugin.json           # plugin manifest
    └── skills/
        └── new-skill/
            └── SKILL.md          # one directory per skill
```

`skills/` is auto-discovered, so adding a skill is just adding a directory with
a `SKILL.md`. A plugin can also carry `commands/`, `agents/`, `hooks/`, and
`.mcp.json` at its root — see the
[plugins reference](https://code.claude.com/docs/en/plugins-reference).

## Add a skill

Create `plugins/agent-skills/skills/<name>/SKILL.md` with frontmatter:

```yaml
---
name: my-skill
description: What it does. Use when <the situation that should trigger it>.
---
```

The `description` is what Claude matches on when deciding to load the skill, so
name the trigger conditions explicitly. The bundled `new-skill` skill walks
through the rest.

## Add another plugin

Create `plugins/<plugin-name>/.claude-plugin/plugin.json`, then add an entry to
the `plugins` array in `.claude-plugin/marketplace.json` pointing at
`./plugins/<plugin-name>`.

## License

MIT — see [LICENSE](LICENSE).
