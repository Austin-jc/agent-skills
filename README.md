# Agent Skills

A collection of [Agent Skills](https://code.claude.com/docs/en/skills) — reusable, model-invoked capabilities that extend Claude with focused expertise for specific kinds of work.

Each skill is a self-contained directory with a `SKILL.md` file. The YAML frontmatter (`name` + `description`) tells Claude when to reach for the skill; the body and any bundled reference files tell it how to do the work.

## Skills

| Skill | What it does |
|---|---|
| [`guided-discovery`](./guided-discovery) | Turns an app, codebase, architecture, concept, task, or product into a scaffolded learning path — coaching a developer to build understanding through guided exploration instead of handing them an answer dump. |

## Using these skills

### Claude Code

Copy (or symlink) a skill directory into a skills location Claude Code reads:

- **Personal** (available in every project): `~/.claude/skills/`
- **Project** (shared with your team via the repo): `.claude/skills/`

```bash
# personal
cp -r guided-discovery ~/.claude/skills/

# or per-project
mkdir -p .claude/skills && cp -r guided-discovery .claude/skills/
```

Claude loads each skill's `name` and `description` and invokes the skill on its own when a request matches. You can also invoke one explicitly with `/guided-discovery`.

### Other agent surfaces

The skills here are plain Markdown and portable. Anywhere that supports the Agent Skills format, point it at the skill directory. The `description` field is what drives automatic triggering, so keep it intact when copying.

## Repository layout

```
<skill-name>/
├── SKILL.md              # frontmatter (name, description) + instructions
└── references/           # optional supporting files loaded on demand
    └── *.md
```

## Adding a skill

1. Create a directory named for the skill (kebab-case).
2. Add a `SKILL.md` with `name` and `description` in the frontmatter. Write the `description` in the third person and be specific about *when* to trigger — that text is all Claude sees when deciding whether to use the skill.
3. Keep `SKILL.md` focused; push long tables, question banks, and templates into `references/` and reference them from the body so they load only when needed.
4. Add a row to the **Skills** table above.

## License

[MIT](./LICENSE)
