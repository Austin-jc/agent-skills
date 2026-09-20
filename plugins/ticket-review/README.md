# ticket-review

A Claude Code skill that brackets every delegated ticket with two plain-language documents:
a **Ticket Brief** before implementation and a **Change Report** after, with deterministic
scripts doing the parsing and the checking so Claude spends context on judgment.

## Install

    /plugin marketplace add austin-jc/agent-skills
    /plugin install ticket-review@agent-skills

That registers the `ticket-review` skill and the `/ticket-brief` and `/change-report`
commands. Add `.ticket-review/` to the `.gitignore` of any repository you use it in.

Optional, for fetching tickets straight from Jira:

    export JIRA_BASE_URL=https://yourcompany.atlassian.net
    export JIRA_EMAIL=you@yourcompany.com
    export JIRA_API_TOKEN=...

## Use

    /ticket-brief BILL-482            # from Jira
    /ticket-brief docs/ticket.md      # from a file or pasted text
    ... approve the task list, let Claude implement ...
    /change-report BILL-482           # from the diff against origin/main

## The scripts, standalone

    python3 skills/ticket-review/scripts/prepare_ticket.py --jira BILL-482
    python3 skills/ticket-review/scripts/inventory_diff.py --base main
    python3 skills/ticket-review/scripts/inventory_diff.py --hunk src/api/checkout.py
    python3 skills/ticket-review/scripts/check_output.py brief  .ticket-review/BILL-482-brief.md
    python3 skills/ticket-review/scripts/check_output.py report .ticket-review/BILL-482-report.md --strict

All standard-library Python 3. Nothing leaves the machine except the optional Jira call.

## Tuning

- `skills/ticket-review/scripts/review_common.py` — `AREA_RULES` maps paths to areas (screens, api, services,
  database, migrations, config, tests). Adjust if your repository's layout differs.
- `skills/ticket-review/scripts/inventory_diff.py` — the regexes at the top detect routes, queries, schema
  statements, environment keys and so on for Python, TypeScript, Rust, Go and common
  frameworks. Add a pattern if your stack's idiom is missing.
- `skills/ticket-review/scripts/check_output.py` — `--allow` for product names that cannot be spelled out;
  `--strict` to make warnings fail. The section lists at the top must match the templates
  in `skills/ticket-review/references/` if you edit either.
