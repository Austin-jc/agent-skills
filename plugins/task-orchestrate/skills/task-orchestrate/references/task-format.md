# Task format & brief assembly (task-orchestrate)

## Annotation grammar

A task is a standard Markdown checkbox line, optionally preceded by a `T<N>` ID, followed by zero or more continuation lines indented at least two spaces:

```
- [ ] T012 <title>
      files: <path>[, <path>...]
      deps: <TID>[, <TID>...]
      verify: <shell command>[; <shell command>...]
      route: codex | direct
      note: <free text>
```

Parser rules (`scripts/tasks.py`):
- A header or any non-indented line ends the current task's annotation block; header sections (Goal/Constraints/Acceptance) pass through untouched, so the plan file parses as a whole.
- IDs are optional overall but required for any task referenced in a `deps:` list.
- `route` omitted → treated as `codex` (shown `codex*`); if codex-delegate isn't available, treat all tasks as `direct`.
- `verify` with multiple commands: semicolon-separated; all must exit 0.
- `[x]` means *verified done* — never pre-check.
- Plain unannotated checklists parse fine: no deps → every unchecked task immediately ready.

Wave semantics: a task is *ready* when unchecked and every dep is checked. `validate` also enforces disjoint `files:` within a wave — the collision boundary that makes parallel or interleaved execution safe.

## Brief assembly (route: codex → codex-delegate)

The plan file is the single context source. Assemble by extraction:

1. **Task** — `python scripts/tasks.py show <plan> T012`: title, files, verify.
2. **Why** — the plan's Goal section, trimmed to what this task needs.
3. **Contract** — interfaces/types this task must conform to: point at the files earlier contract-tasks produced (paths, not dumps) plus any relevant Constraints lines. `[protected]` constraints go in verbatim.
4. **Acceptance criteria** — the task's `verify:` command(s); add "existing tests still pass" when cheap.
5. **Out of scope** — sibling task titles from the same plan (so the executor doesn't helpfully implement T013), plus standard exclusions: no unrelated refactors, no new dependencies, no formatting churn.

Target: well under a screen. If a brief needs substantial new prose, the plan header is underspecified — fix the plan (cheaper than debugging a misimplementation) or route the task `direct`.

## Repair bookkeeping

Append the falsified hypothesis to `note:`, not just "failed":

```
      note: attempt1(codex): matchMedia listener leaks on unmount — teardown test failed
```

Second failure → set `route: direct`, keep notes, implement with them in view. Contract-mismatch failures (decomposition wrong, not code wrong): adjust the affected tasks' annotations, uncheck only invalidated tasks, record why.

## Worked example

```markdown
# Plan: rate-limit public API
intake: JIRA PLAT-4312

## Goal
Add per-key rate limiting to public REST endpoints; 429 + Retry-After on
breach; limits configurable per tier.

## Constraints
- [protected] Redis-backed sliding window; no new infra
- Middleware pattern per src/middleware/auth.ts

## Acceptance
- npm test
- npx tsc --noEmit

## Tasks

### Contracts
- [ ] T001 Define RateLimiter interface + tier config types
      files: src/ratelimit/types.ts, config/tiers.ts
      verify: npx tsc --noEmit

### Implementation
- [ ] T002 Redis sliding-window limiter implementing RateLimiter
      files: src/ratelimit/redis.ts
      deps: T001
      verify: npm test -- ratelimit
- [ ] T003 Express middleware + 429/Retry-After handling
      files: src/middleware/ratelimit.ts
      deps: T001
      verify: npm test -- middleware
- [ ] T004 Wire middleware into route registry
      files: src/routes/index.ts
      deps: T002, T003
      verify: npm test

### Verification
- [ ] T005 Integration test: tier limits + header correctness
      files: test/integration/ratelimit.spec.ts
      deps: T004
      verify: npm test -- integration/ratelimit
```

Waves: {T001} → {T002, T003} → {T004} → {T005}. T002/T003 dispatch as independent codex-delegate runs with zero collision risk.
