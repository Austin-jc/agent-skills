# Writing rules for the Ticket Brief and Change Report

The reader has never seen this codebase and does not know this business. Everything is written for them.

## Why these documents exist

- **The business disconnect.** Code that solves the prompt but not the operational problem, because nobody stated who suffers when it fails or what assumption was made along the way.
- **The code fog.** A summary so vague it says nothing ("updated the service layer") or so low-level it is the diff again. Both defeat a fast review.
- **The silent blast radius.** Backend changes, database side effects and screen changes with no trail of where to look or how to see them working.

## Audience

- Assume no prior context about the system or the business.
- Spell out every term the first time: "application programming interface (API)" then "API" is fine. Never use an abbreviation before spelling it out. Technical terms are fine once defined; the goal is clarity, not avoiding the word "endpoint."
- Define every business term the first time it appears, in the sense this business uses it. "Account" means different things in different companies; say which.
- Never use placeholder labels: no "Option A," "Service B," "Step 1a," no "the user." Use real names of files, screens, tables, roles and services.

## Format

- Bullets. Prose only where a bullet cannot carry the idea.
- One to three sentences per bullet. Task bullets have three parts (what, why, where) and may use three sentences; nothing else should.
- Every item states both **what** and **why**. A change or task with no reason is incomplete.
- Concrete beats abstract: "a billing coordinator looking at the Acme Corp account" beats "a user viewing an account."
- Quantify where possible: how many people, how often, how many rows, how long.
- A section with nothing in it gets one line saying so. Do not pad.
- Headings are `## N. Section name`, numbered, in the template order. The gate checks them.
- File names, paths, environment keys and setting names go in backticks. Expressions, calls and queries never do.

## Level of detail — the conceptual rule

Describe what code does. Never paste it. State the purpose, what it operates on, what it filters or decides on, and what it produces. Applies to queries, logic and screens alike.

**Queries**
- Too vague: "Updated the client query to improve dashboard loading."
- Too low-level: `SELECT c.id, SUM(a.value) FROM clients c JOIN accounts a ...`
- Right: "Added a query that joins the clients table to the accounts table and returns the top one hundred clients ranked by total contract value, limited to accounts active in the last ninety days."

**Logic**
- Too vague: "Added invoice validation."
- Right: "Added a rule that blocks an invoice from being sent if the account has an unpaid balance older than sixty days, and shows the sender a message naming the overdue amount."

**State changes**
- Too vague: "Updated the status handling."
- Right: "Moves the application from Submitted to Under Review only after all three identity documents are uploaded; before this change it moved on upload of the first one."

**Screens**
- Too vague: "Updated the checkout page."
- Right: "On the checkout page, above the payment section, a red notice card now appears when the account is overdue. The Complete Order button below it is greyed out. Before this change no notice existed and the button was always active."

## Honesty

- If something is unknown, write "This is not stated in the ticket" or "I assumed this — please confirm." Never present a guess as fact.
- No filler: no "robust," "seamless," "leverage," "streamline," "utilize."
- No hedging in place of a decision. "Probably" and "seems to" are replaced by either a plain statement or a flagged assumption.
