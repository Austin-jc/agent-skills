# Agent Skills

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) that distributes [Agent Skills](https://code.claude.com/docs/en/skills) — reusable, model-invoked capabilities that extend Claude with focused expertise for specific kinds of work.

Each skill ships as its own installable plugin, so you can add just the ones you want. Marketplace name: **`jc-agent-skills`**.

## Plugins

| Plugin | What it does |
|---|---|
| [`guided-discovery`](./plugins/guided-discovery) | Turns an app, codebase, architecture, concept, task, or product into a scaffolded learning path — coaching a developer to build understanding through guided exploration instead of handing them an answer dump. |
| [`task-orchestrate`](./plugins/task-orchestrate) | Turns a task, ticket, issue, or requirements doc into a dependency-aware, verifiable, executor-routed plan file, then drives it to completion in dependency waves with per-task verification. |

## Install

Add the marketplace once, then install any plugin from it:

```
/plugin marketplace add Austin-jc/agent-skills
/plugin install guided-discovery@jc-agent-skills
/plugin install task-orchestrate@jc-agent-skills
```

Pull in new or updated plugins later with `/plugin marketplace update jc-agent-skills`.

Once installed, Claude reads each skill's `name` and `description` and invokes it on its own when a request matches. You can also trigger one explicitly with its slash command, e.g. `/guided-discovery`.

### Use a skill without the marketplace

The skills are plain, portable Markdown. To use one directly, copy its `SKILL.md` (and any `references/`) into a skills location Claude Code reads:

- **Personal** (every project): `~/.claude/skills/`
- **Project** (shared via the repo): `.claude/skills/`

```bash
cp -r plugins/guided-discovery/skills/guided-discovery ~/.claude/skills/
```

## Repository layout

```
agent-skills/                                  # marketplace root
├── .claude-plugin/
│   └── marketplace.json                       # catalog of plugins
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json                    # plugin manifest
        └── skills/
            └── <skill-name>/
                ├── SKILL.md                   # frontmatter (name, description) + instructions
                └── references/                # optional files loaded on demand
```

## Adding a skill

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json` manifest (`name` is the only required field; add `version`, `description`, `author`, `license`, `keywords`).
2. Put the skill under `plugins/<name>/skills/<name>/SKILL.md`. Write the `description` in the third person and be specific about *when* to trigger — that text is all Claude sees when deciding whether to use the skill. Push long tables, question banks, and templates into `references/` so they load only when needed.
3. Register the plugin in `.claude-plugin/marketplace.json` with a `./plugins/<name>` source, and add a row to the **Plugins** table above.
4. Validate before publishing: `claude plugin validate ./plugins/<name> --strict`.

> **Note:** the marketplace is named `jc-agent-skills`, not `agent-skills` — the latter is a [reserved name](https://code.claude.com/docs/en/plugin-marketplaces) for official Anthropic use.

## License

[MIT](./LICENSE)
