---
name: task-orchestrate
description: Turn any task, ticket, issue, or requirements into a dependency-aware, verifiable, executor-routed plan and drive it to completion. Use when the user asks to "break this down", "plan this", "orchestrate", implement a ticket/issue/feature/requirements doc, or when a coding task is clearly multi-step and no dedicated spec-workflow tool governs the repo. Works standalone with a single self-contained plan file; composes with codex-delegate for delegated execution. If the repo uses OpenSpec (openspec/ directory) and the openspec-orchestrate skill is available, prefer that skill instead.
---

# Task Orchestrate

Take an intake (ticket, issue, verbal requirements, a paragraph in chat) and produce a **self-contained plan file**, then execute it in dependency waves with per-task verification. Everything an executor needs lives in one file — portable across sessions, tools, and agents.

Grounding (why these rules): task accuracy collapses past one working set (~87% single-function vs ~19% multi-file in reported evals); over-decomposition and over-specification are measured failure modes, so plan depth must match task size; unverified checkboxes let defects propagate; failures should trigger local repair, never global replanning.

## Step 0: Should this be orchestrated at all?

No, if the task fits one working set (one interface seam, ~1–3 files, one clear verify). Just do it or send it straight through codex-delegate. A plan file for a small task is overhead dressed as diligence. Orchestrate when the work spans multiple seams, has real ordering constraints, will outlive one session, or the user asks for a plan.

## Step 1: Intake → plan file

Extract from the intake (read tickets/issues/docs the user points at; don't ask for what's already written):
- **Goal** — what done means, one paragraph
- **Constraints** — tech choices, conventions, hard requirements; mark non-negotiables `[protected]` (executors may adapt anything else)
- **Acceptance** — runnable commands that prove the whole plan (full test suite, typecheck, build)
- Open decisions the intake genuinely doesn't settle → ask the user (once, batched), or mark a `route: direct` decision task

Write to `plans/<slug>/tasks.md` (or a user-preferred location; keep it in-repo so it versions with the code):

```markdown
# Plan: <title>
intake: <ticket URL / issue # / "conversation 2026-08-08">

## Goal
...

## Constraints
- [protected] Use the existing Postgres instance; no new datastores
- Follow src/lib/ error-handling pattern

## Acceptance
- npm test
- npx tsc --noEmit

## Tasks
- [ ] T001 ...
```

## Step 2: Decompose

1. **One working set per task** — completable reading only its `files:` plus this plan file's header. If a task description needs "and then also…", split it.
2. **Cut along interface seams, not feature narrative.** Contracts/types/interfaces first; conforming implementations after, parallel where files are disjoint. Children of a split must sum to the parent — no orphaned or overlapping responsibility.
3. **Every implementation task gets `verify:`** — a runnable command. No check exists? Add the task that creates one *first*; a test is a cheaper reviewer than any model. Decision tasks (`route: direct`) may omit it.
4. **Route by judgment density.** Mechanical implementation from a clear contract → `codex`. Design decisions, security-sensitive logic, subtle concurrency, heavy conversation-context tasks → `direct`. Unsure → codex; review catches it.
5. **Depth matches size.** 3 tasks for a bugfix, not 15. Prefer fewer, meatier tasks over confetti; split later if one fails (lazy decomposition beats exhaustive upfront).

Task annotation format (full grammar in references/task-format.md):

```markdown
- [ ] T002 Theme provider with system-preference detection
      files: src/theme/context.tsx, src/theme/index.ts
      deps: T001
      verify: npm test -- theme
      route: codex
```

Then lint: `python scripts/tasks.py validate plans/<slug>/tasks.md` — catches unknown deps, cycles, duplicate IDs, same-wave file overlaps. Show the user the plan (waves + task list) before executing unless they've told you to just go.

## Step 3: Execute

Preflight: codex-delegate check if any task routes to codex (clean worktree, codex authed); if unavailable, reroute all `direct` and say so.

Loop:
1. **Wave:** `python scripts/tasks.py ready <plan>` — unchecked tasks with all deps satisfied, grouped by route. Same-wave tasks are independent by construction (disjoint `files:`).
2. **Dispatch:** `codex` → assemble a brief from the plan file (recipe in references/task-format.md — mostly extraction: task block + Goal + binding Constraints + verify as acceptance) and run through codex-delegate. `direct` → implement yourself, scoped to `files:`.
3. **Verify before checking.** Run the task's `verify:`; only on exit 0 mark `[x]`. A checkbox is a verified claim, not a progress note.
4. **Repair locally.** Failure → one focused correction (codex-delegate `followup`). Second failure of the same task → reroute `direct`, take over. Either way append the falsified hypothesis to `note:` — what didn't work is load-bearing context. If failure reveals wrong *decomposition* (contract mismatch between tasks), fix only the affected subgraph: adjust annotations, uncheck only invalidated tasks, note why. Never rewrite tasks that passed.
5. When `python scripts/tasks.py status <plan>` shows all done → run the plan's Acceptance commands, report the verdict + diffstat, suggest a commit.

## Session continuity

The plan file is the handoff artifact. A fresh session resumes with: read the plan file, run `status` and `ready`, continue the loop. Never rely on conversation memory for plan state — if it isn't in the file, it didn't happen.

## Adapting to existing structure

- Existing checklist (TODO.md, a ticket's task list): don't rewrite it — annotate remaining unchecked items in place, add a Goal/Constraints/Acceptance header if missing, validate, proceed.
- Repo has its own SDD tool (OpenSpec etc.): defer to that tool's artifacts as the context source; use its dedicated orchestration skill if installed.

## Reference

- `references/task-format.md` — annotation grammar, brief assembly recipe, repair bookkeeping, worked example.
- `scripts/tasks.py` — `validate | ready | status | waves | show <ID>`.
