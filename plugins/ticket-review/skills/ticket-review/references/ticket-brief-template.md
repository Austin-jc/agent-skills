# Ticket Brief — template

File: `.ticket-review/<KEY>-brief.md`. Title line: `# Ticket Brief — <KEY> <title>`. Sections use exactly these headings, in this order.

## 1. At a glance
- Ticket type: new feature, change to an existing feature, bug fix, refactor, data change, or maintenance.
- The request in one sentence. The business reason in one sentence.
- Rough size: hours, days, or more than a week.

## 2. Words you need to know
- Every business term the ticket uses (start from `glossary-candidates.md`), defined in plain language as this business uses it. Say "generic term" for the ones that need no definition, so the reader knows you considered them.
- Where two terms sound similar, explain the difference.
- Any internal system or tool named, with one line on what it is for.

## 3. Why this exists
- The business process this sits inside: who does it, how often, what it is for.
- The specific friction: what goes wrong, is slow, is missing, or is risky.
- Who runs into it — the actual role, such as "billing specialists reconciling end-of-month payments," never "the user."
- How often, and what it costs in time, money, errors or risk. Use numbers if any are given.
- The cost of inaction: what gets worse if this is never built.
- Who asked and what outcome they expect afterward.
- Standalone or part of a larger effort. If larger: name it, its goal, what came before, what comes next. Include linked tickets and how they relate.
- If the ticket does not explain the business reason, say so plainly. Do not invent one.

## 4. Before and after
- **Before:** a real role in a realistic example, step by step, with the exact step where the problem appears marked.
- **After:** the same situation once this ships, with the difference marked.
- Keep the two parallel. This is the section most people actually read.

## 5. Scope and anti-scope
- What exactly is being asked, precisely, now that the reader has context.
- What is explicitly included.
- What must **not** change: existing behaviours to preserve, adjacent screens, endpoints and rules to leave alone. Derive this from the candidate files, not only from the ticket. This is the fence against scope creep.

## 6. Triggers, inputs, outputs, and failure
- **Trigger:** the action or event that starts this.
- **Inputs:** what information must be present, as business data ("the customer's email address and invoice number"), not data types. Required versus optional, and what makes a value valid.
- **Outputs:** what is created or changed — records, notifications, files, what the person sees.
- **Failure:** what should happen when input is wrong or empty, data is missing, or an outside service is down. If the ticket is silent, propose the safe behaviour and flag it as an assumption.

## 7. The work involved
- Tasks in the order they should happen.
- Each task: what it changes, why that change is needed to deliver the ticket, and which file or service it lives in (in backticks) with what that part is responsible for today.
- Mark uncertain or risky tasks and tasks with more than one possible approach with a bullet starting "Uncertain:" or "Choice:", and state the recommendation.
- This is the list the reader approves before implementation. A task that cannot be explained in terms of the business reason probably does not belong.

## 8. What done looks like
- Conditions that must be true for this to be finished, as plain sentences a non-engineer could check. Include the failure paths from section six.

## 9. Assumptions, open questions, and what could break
- Things assumed in order to proceed, each starting "Assumption:" and ending "please confirm." Be generous — unstated assumptions are the root of the business disconnect.
- Things the ticket does not answer, and who could answer each.
- Other features or teams that depend on the code being changed, and the realistic failure cases.

## 10. Self-check
- Someone with no knowledge of this business could explain in two sentences why this ticket exists.
- The walkthrough uses a real role and a concrete example.
- Every task states why it is needed and where it lives.
- Every business term is defined in section two. No abbreviation appears unexplained.
- Nothing assumed is presented as fact.
