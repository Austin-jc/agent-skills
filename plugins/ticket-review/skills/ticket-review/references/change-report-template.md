# Change Report — template

File: `.ticket-review/<KEY>-report.md`. Title line: `# Change Report — <KEY> <title>`. Written from the diff (`inventory.md` plus `--hunk` reads), not from memory of the session. Sections use exactly these headings, in this order.

## 1. Summary, and asked versus built
- Three to five bullets on what now exists that did not before.
- One bullet per scope item from the Ticket Brief: delivered fully, partly, or not at all. If there is no brief, use the ticket's acceptance criteria.
- Anything built that was not asked for, anything done differently from the approved task list, anything crossing the anti-scope fence — each with the reason.

## 2. How it works, end to end
- One bullet per hop, from what the person or system does to trigger it, through the screen, the request, the service, the rules applied, the data read or written, to what comes back.
- Written as a story: actor, action, what the system does, result. See the example report for the register.
- Each path traced separately: success, blocked, error.

## 3. User interface
One line "No screen changes." if none. Otherwise, for each screen or component that changed:
- **Which screen** — the name a user would recognise, not the component filename.
- **How to get there** — the exact click path from the starting page.
- **Before versus after** — what was there, what is there now, and where on the screen.
- **Interactive states** — on click, on typing, while loading, when empty, when something fails.
- **Conditions** — if it only appears for certain roles, plans or data states, say exactly which.

## 4. Endpoints and service interfaces
One line if none. Otherwise for each: added, changed or removed; the path; what it does in plain words; what it expects and returns; who calls it. If changed: what was different before and whether any caller must be updated. Use `inventory.md`'s endpoint list and the "existing functions whose body was edited" list so that a route whose body changed but whose declaration did not is not missed.

## 5. Business rules and logic
One line if none. Otherwise:
- **New validation:** the condition enforced and what happens when it fails, including the message the person sees.
- **State transitions:** how a status moves and what must be true for it to move.
- **Changed rules:** before versus now.
- **Bug fixes:** what was going wrong, what the person saw, what now happens.
- **Refactoring:** what was moved, renamed, split or merged, and why. End with "Behavior is unchanged; this is a structural change only" — or say what changed.

## 6. Data
One line if none. Otherwise:
- **New or changed queries**, conceptually: what it links, calculates, filters on, sorts by, roughly how many rows, and what business question it answers. For changed queries, before versus now.
- **New facts stored:** what the system now records that it did not before.
- **Schema and migrations:** tables, columns, indexes; what the migration does, whether it moves data, whether it reverses safely, roughly how long it runs.
- **Performance:** anything reading a lot of data and what was done about it.

## 7. Configuration and flags
One line if none. Otherwise: new settings or environment keys (in backticks), what each controls, the value each environment needs; feature flags and whether the new behaviour is currently on; anything that must be set before deployment.

## 8. Tests, and where to find everything
- Each test added or changed, described by what it proves.
- What is not covered and needs a manual check.
- Every file added, changed or deleted, in backticks, grouped by area, with one line on what the file is responsible for and what changed in it. `inventory.md` has the list; you supply the words.

## 9. Manual verification recipe, and what was not done
- Numbered steps a non-engineer can follow, starting with setup: which account, which test record, which flag.
- The happy path with what a correct result looks like.
- At least one failure or edge case with what the correct failure looks like.
- Anything from the ticket deliberately left out and why; known rough edges, temporary shortcuts, follow-up work worth its own ticket — or a line saying nothing was left out.

## 10. Risk, watch list, and self-check
- What is most likely to go wrong. Which existing features touch the changed code and should be spot-checked. What to watch in logs or dashboards on day one.
- Self-check line: written from the diff; every hop traced in section two; no code pasted; every screen change has a click path; every deviation is in section one; no abbreviation unexplained.
