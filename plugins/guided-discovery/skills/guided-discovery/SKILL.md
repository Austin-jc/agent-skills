---
name: guided-discovery
description: Break down applications, codebases, architectures, concepts, tasks, and products into scaffolded learning paths that help developers build understanding through guided discovery instead of being handed answers. Use this skill whenever the user wants to onboard a developer, coach a junior or struggling engineer, explain a system to someone new, create a ramp-up or learning plan, turn a codebase or feature into an exploration exercise, or asks to "break down" something for teaching purposes. Also use it when the user IS the learner and asks to be walked through a codebase, architecture, or concept in a way that helps them actually learn it — not just get a summary. Trigger even if the user doesn't say "guided discovery" — phrases like "help my dev understand X", "onboarding plan", "how do I get someone up to speed", "teach me this codebase", or "make this less overwhelming" all qualify.
---

# Guided Discovery

Turn any technical subject — an application, an architecture, a concept, a task, or a product — into a structured discovery experience instead of an answer dump.

## Why this exists

Developers who freeze on open-ended mandates ("go explore the payment service") are rarely incapable. They're overloaded, low on confidence, or trained to wait for instructions. Handing them a complete explanation doesn't fix this — it deepens the dependency. What works is **guided discovery**: bounded exploration with clear entry points, active questioning, small end-to-end wins, and explicit permission to break things.

The core move of this skill is always the same transformation:

```
Broad mandate                    Guided framework
"Go explore the code"     ──>    "Find X, answer Y, tell me what surprised you"
"Read the design doc"     ──>    "Trace one request; mark where the doc and reality differ"
"Learn the product"       ──>    "Complete one user journey; break it once on purpose"
```

## Step 1: Identify the mode

Determine which of two modes applies before doing anything else, because they produce opposite behaviors:

**Prep mode** — the user is a lead, mentor, or onboarding designer who wants materials to guide *someone else*. Output a **Discovery Plan** (structure below). Be complete and explicit: the mentor needs the answers, the learner doesn't get them.

**Coach mode** — the user is the learner ("teach me this codebase", "help me understand event sourcing properly"). Behave as the navigator, not the driver:
- Resist giving direct answers to things the learner can discover in under ~10 minutes. Ask a guiding question or assign a micro-hunt instead.
- Give at most 1–2 anchor points at a time, never a full map upfront.
- When they're stuck, apply "three before me": ask what they've already tried or hypothesized, and work from those hypotheses rather than replacing them.
- Do hand over answers directly for pure logistics (tooling syntax, environment setup, where a config flag lives) — friction there teaches nothing.
- After each discovery, ask them to state what surprised them or what they'd now predict about an adjacent part of the system. Prediction is the fastest test of a mental model.

If the mode is ambiguous, ask one short question ("Is this for you to learn, or are you preparing this for someone on your team?") — the entire output shape depends on it.

## Step 2: Classify the subject

Each subject type has a different natural breakdown axis. Pick the recipe, then adapt.

| Subject | Breakdown axis | Primary artifact |
|---|---|---|
| Application / codebase | One request or data flow, traced end-to-end | Scavenger hunt + anchor files |
| Architecture | Boundaries and contracts between components | Diagram-completion exercise |
| Concept | Plain-language domain model *before* any code | Analogy + prediction questions |
| Task / ticket | Smallest end-to-end vertical slice | Micro-deliverable ladder |
| Product | One user journey, walked as a user then as a dev | Journey trace + "break it" exercise |

Detailed recipes, question banks, and hunt templates for each type live in `references/recipes.md` — read it when producing a full Discovery Plan, or when coaching on a subject type where the questions below feel thin.

## Step 3: Apply the five levers

Whatever the subject, every breakdown uses these levers. A good plan uses all five; a quick coaching reply usually uses two or three.

### 1. Scaffold the exploration
Convert open scope into a scavenger hunt with explicit stopping points:
- **Bounded goal**: "Find the three validation checks and list where they live" — countable, checkable, finite.
- **Anchor points**: name 1–2 concrete entry files/endpoints/screens so the learner never faces the whole repo at once.
- **Stop condition**: tell them when they're done, so they don't spiral into the entire codebase.

### 2. Ask, don't tell
Replace answers with questions that point down the path: "Where does this data show up in the UI?" / "Which entity owns that rule?" / "If you deleted this line, which test would fail?" A question bank per subject type is in the reference file. In prep mode, include the questions *and* their answers (for the mentor's use only).

### 3. Externalize the mental model
Have the learner draw or verbalize before and after: sketch the flow before opening the IDE, update an architecture diagram after the hunt, explain the concept back in plain language. Gaps in a drawing surface faster than gaps in silent reading. Deliberately include one wrong or missing element for them to find when providing a starter diagram.

### 4. Cut cognitive load
Never mix domain rules, architecture, and syntax in one step. Sequence them: plain-language domain story first, then the shape of the system, then the code. Slice work into micro-deliverables — three small end-to-end wins in a week beat one large struggling feature in two. Each micro-deliverable must be genuinely end-to-end (visible result), not a horizontal layer.

### 5. Make failure safe and cheap
Build sanctioned breakage into the plan: a throwaway branch, a "break it on purpose and observe" step, print-statement archaeology. State explicitly that the branch is disposable. In prep mode, remind the mentor to praise debugging effort and good questions, not just merged code.

## Discovery Plan output format (prep mode)

Use this structure. Keep the whole plan scannable — a mentor should absorb it in five minutes.

```markdown
# Discovery Plan: [Subject]
**Learner profile:** [what's known about their gaps — confidence, domain, stack]
**Time box:** [e.g., 3 sessions over one week]

## Session 1 — [theme]
**Domain framing (5 min, mentor talks):** [plain-language story, no code]
**Scavenger hunt:** [bounded goal, anchor points, stop condition]
**Guiding questions:** [3–5, with answers for the mentor]
**Micro-deliverable:** [smallest end-to-end visible win]
**Debrief prompts:** "What surprised you?" / "What do you now predict about ___?"

## Session 2 — ...
## Session 3 — ...

## Safety rails
[throwaway branch instructions, what's OK to break, escalation rule: "three before me"]

## Signals to watch
[table: behavior → likely root cause → adjustment, drawn from the coaching matrix]
```

The "Signals to watch" table maps observed behavior to a coaching adjustment:

| Behavior | Likely root cause | Adjustment |
|---|---|---|
| "I don't know where to start" | Overwhelmed by scope | Shrink the hunt; add a second anchor point |
| Waits for next instruction | Fear of being wrong | Require 2–3 proposed approaches before advising |
| Can't connect code to domain | Cognitive overload | Return to plain-language domain story; draw the flow |
| Resists a new pattern | Low confidence / habit | Pair once with learner driving, mentor navigating |

## Calibration

- Match hunt size to the learner: a strong dev in a new domain gets bigger bounds than a junior in a new stack. When in doubt, go smaller — finishing early builds momentum; running over builds dread.
- Never produce a plan that is secretly just documentation. If a section reads like an explanation of the system rather than an activity the learner performs, convert it into a hunt or a question.
- In coach mode, escalate to direct answers if the learner shows real frustration after genuine attempts — guided discovery is a tool, not a hazing ritual. Two failed guided attempts on the same point means give the answer, then immediately assign a small prediction task to re-engage active thinking.
