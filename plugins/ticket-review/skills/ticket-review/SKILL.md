---
name: ticket-review
description: Two-phase review system for tickets that Claude implements — a Ticket Brief before any code is written (business context, before-and-after walkthrough, task list to approve) and a Change Report after (end-to-end flow, every endpoint, query, rule and screen change described in plain words, with a click path and a manual verification recipe). Use this whenever the user gives you a ticket, issue, story or Jira key to understand or start on, asks what a ticket is really about, asks you to explain, summarize or audit what was implemented on a branch or in a pull request, or says "brief", "change report", "what did we change", "walk me through this ticket", "review this before you start", or "what did you actually build". Also use it when a user who delegates implementation asks to understand a task in plain language. Do not skip it because the ticket looks small.
---

# Ticket Review

The person you are writing for delegates implementation and does not read code. They need two documents per ticket:

1. **Ticket Brief** — before implementation. What is being asked, why anyone cares, what work it takes. Ends with a task list they approve.
2. **Change Report** — after implementation, written from the diff. What was built, how it works end to end, how to see it.

Both are plain language, bullets, concrete, with a reason on every line. The full templates and writing rules are in `references/`. Read them — the section names are checked by a script and must match exactly.

Three scripts do the deterministic parts so that you spend context on judgment, not on parsing:

| Script | Phase | What it saves you |
|---|---|---|
| `scripts/prepare_ticket.py` | before the brief | Normalizes the ticket, pulls out glossary terms, and lists the files in the repo that mention them, ranked. You read those files, not the whole repo. |
| `scripts/inventory_diff.py` | before the report | Turns the diff into a classified inventory: files by area, endpoints, queries, schema, config keys, validation, state changes, screen text, tests. You read the inventory, then pull hunks one file at a time. |
| `scripts/check_output.py` | after either document | Fails the document if a section is missing, empty, or out of order, if code or SQL is pasted, if a placeholder or abbreviation slipped in, or if a mode-specific requirement is unmet. You fix and re-run until it passes. |

All three are standard-library Python and run from the repository root. Output goes to `.ticket-review/` in the repo (add it to `.gitignore`).

## Mode: Ticket Brief

Trigger: the user hands you a ticket and wants to understand it or is about to have you implement it.

1. **Run the pre-phase.** Give it whatever you have: `--jira KEY` (needs `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`), `--file path` for pasted or exported text, or pipe the text on standard input. Save pasted text to a file first.
   ```
   python3 <skill>/scripts/prepare_ticket.py --file .ticket-review/raw-ticket.md
   ```
   It prints and saves `ticket.md` (normalized, with acceptance criteria and comments split out), `glossary-candidates.md`, and `candidate-files.md`.
2. **Read the normalized ticket**, not the raw one. If it says acceptance criteria were not found, the brief must say so — do not invent them.
3. **Read only the candidate files**, top few per area. Read the parts that touch the ticket's terms; you do not need whole files. Open a file outside the list only if one of these points at it. The goal is to know where the work lives and what must not change, not to understand the whole system.
4. **Write the brief** to `.ticket-review/<KEY>-brief.md` using `references/ticket-brief-template.md`. Use `## 1. At a glance` style headings exactly. Define every glossary candidate in section two or state it is generic. Every task in section seven says what, why, and which file it lives in.
5. **Run the gate** and fix until it passes:
   ```
   python3 <skill>/scripts/check_output.py brief .ticket-review/<KEY>-brief.md
   ```
   Each error names the line and what to change. Fix the document, not the checker. If an abbreviation is a real product name that cannot be spelled out, pass `--allow NAME` and say why in your reply. Three passes is usually enough; if a rule keeps failing, the content is missing, not the phrasing.
6. **Stop.** Present the brief. Do not implement. The task list in section seven is what the user approves; wait for that before writing code.

## Mode: Change Report

Trigger: implementation is done on a branch, or the user asks what was built.

1. **Run the pre-phase** from the repository root:
   ```
   python3 <skill>/scripts/inventory_diff.py                # auto-detects origin/main etc.
   python3 <skill>/scripts/inventory_diff.py --base main    # or name the base
   python3 <skill>/scripts/inventory_diff.py --working-tree # include uncommitted work
   ```
   It prints `inventory.md`: commit messages, files by area, and every signal it could extract. It also saves `diff.patch` for the next step.
2. **Read the inventory first.** It is a few hundred tokens and tells you where to look. Do not read `diff.patch` directly.
3. **Pull hunks one file at a time**, only for files the report needs to describe:
   ```
   python3 <skill>/scripts/inventory_diff.py --hunk src/api/checkout.py --max-lines 200
   ```
   Files in `screens`, `api`, `services`, `database` and `migrations` almost always need a look. `tests` and `config` usually only need the inventory line. Skip `docs` unless the ticket is about docs. If a hunk is truncated and the file matters, raise `--max-lines`; if it does not, move on.
4. **Read the Ticket Brief** if one exists in `.ticket-review/`, so section one can compare asked versus built.
5. **Write the report** to `.ticket-review/<KEY>-report.md` using `references/change-report-template.md`. Write from the diff, not from your memory of the session — the work may have spanned sessions or been compacted. Section two (how it works, end to end) is the section the user reads first; trace every hop.
6. **Run the gate** and fix until it passes:
   ```
   python3 <skill>/scripts/check_output.py report .ticket-review/<KEY>-report.md
   ```
7. **Present the report.** Lead with section two in your reply if you summarize at all; otherwise just point at the file.

## Token discipline

The scripts exist so that you never read a whole diff or a whole repository to write these documents. Concretely:
- Never `cat` a file when the inventory already tells you what changed in it and the change is small.
- Never read `diff.patch`. Use `--hunk`.
- Never grep the repo yourself for ticket terms; `prepare_ticket.py` already did, with ranking.
- When a hunk is truncated, decide from the inventory whether the file matters before raising the limit.
- Read the templates once per document, not per section.

## Writing discipline

The gate enforces the mechanical rules. These are the ones it cannot check:
- **The reason is the content.** A bullet that says what changed but not why is a diff line in English. If you cannot state the why, you do not understand the change yet — go back to the hunk.
- **Concrete beats general.** A named role in a named situation. "A purchasing coordinator at a client with a two-month-old unpaid invoice" tells the reader more than "a user with overdue invoices."
- **The end-to-end flow is a story.** Actor, action, what the system does, what comes back. If a hop is missing the reader cannot follow it, and the document has failed even if the gate passes.
- **Say what you do not know.** "Not stated in the ticket" and "assumed — please confirm" are correct answers. A confident guess is the failure mode this whole system exists to prevent.

## References

- `references/writing-rules.md` — the shared rules, with good and bad examples for queries, logic, and screens. Read before writing either document.
- `references/ticket-brief-template.md` — the ten sections of the brief and what goes in each.
- `references/change-report-template.md` — the ten sections of the report and what goes in each.
- `references/example-brief.md` and `references/example-report.md` — complete examples that pass the gate, for calibrating length and depth. Skim once; do not copy their content.
