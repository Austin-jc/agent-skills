# agent-skills

A Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
hosting Austin's agent skills.

## Install

```
/plugin marketplace add austin-jc/agent-skills
/plugin install ticket-review@agent-skills
```

Update later with `/plugin marketplace update`. To try local changes before pushing,
add the clone path instead: `/plugin marketplace add ./path/to/agent-skills`.

## Plugins

| Plugin | What it does |
|---|---|
| [`ticket-review`](plugins/ticket-review) | A plain-language **Ticket Brief** before implementation and a **Change Report** after, for people who delegate implementation and do not read code. Ships `/ticket-brief` and `/change-report`, plus scripts that normalize the ticket, classify the diff, and fail a document that breaks the template. |

## Layout

```
.claude-plugin/
└── marketplace.json              # marketplace manifest — lists the plugins below
plugins/
└── ticket-review/
    ├── .claude-plugin/
    │   └── plugin.json           # plugin manifest
    ├── commands/                 # slash commands
    └── skills/
        └── ticket-review/
            ├── SKILL.md
            ├── references/       # templates and examples, read on demand
            └── scripts/          # standard-library Python helpers
.claude/skills/                   # skills for working on THIS repo, not shipped
```

`skills/` and `commands/` are auto-discovered, so adding a skill to a plugin is just
adding a directory with a `SKILL.md`. A plugin can also carry `agents/`, `hooks/`, and
`.mcp.json` at its root — see the
[plugins reference](https://code.claude.com/docs/en/plugins-reference).

## Add a plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with at least a `name`.
2. Add skills under `plugins/<name>/skills/<skill>/SKILL.md`.
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json` pointing at
   `./plugins/<name>`.
4. Validate: `claude plugin validate .` and `claude plugin validate ./plugins/<name>`.

The `new-skill` skill in `.claude/skills/` walks through the details and loads
automatically when you work in this repo.

## License

MIT — see [LICENSE](LICENSE).
