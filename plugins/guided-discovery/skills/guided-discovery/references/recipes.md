# Breakdown Recipes by Subject Type

Read the section matching the classified subject. Each recipe gives the breakdown sequence, a hunt template, and a Socratic question bank. Questions marked (A) should ship with answers in prep mode.

## Contents
1. Application / codebase
2. Architecture
3. Concept
4. Task / ticket
5. Product

---

## 1. Application / Codebase

**Breakdown axis:** one concrete flow, traced end-to-end. Never breadth-first ("read the services"); always depth-first on a single request or data path, because a single completed trace gives the learner a spine to hang everything else on.

**Sequence:**
1. Pick the flow with the highest domain relevance-to-complexity ratio (often: the main read path, not the write path).
2. Name the two anchor points: where the flow enters (route/controller/handler) and where it lands (table/queue/external call).
3. Hunt: trace entry → landing, collecting a fixed list of findings.
4. Externalize: learner draws the trace as boxes and arrows from memory, then checks.
5. Micro-deliverable: a one-line change with visible effect on that flow (log line, copy change, new field surfaced).

**Hunt template:**
> Trace a single [X] request from `[entry file]` to `[destination]`. Along the way, find: (a) the [N] validation checks and where each lives, (b) the point where the domain object is constructed, (c) one thing that surprised you. Stop when you reach `[destination]` — don't follow side effects yet.

**Question bank:**
- Where does this data show up in the UI? (A)
- Which module would you edit to change [specific business rule]? (A)
- If you deleted this line, which test fails? (A)
- What happens to this request if [dependency] is down? (A)
- Which parts of this trace are framework, and which are ours?
- Where would you put a breakpoint to see the moment [decision] is made? (A)

**Break-it exercise:** on a throwaway branch, make the flow fail three different ways (bad input, disabled dependency, deleted validation) and record the error surface for each. Failure modes teach the boundaries faster than the happy path teaches the middle.

---

## 2. Architecture

**Breakdown axis:** boundaries and contracts. Learners drown in architecture when they try to hold every component; they float when they understand what each edge *promises*.

**Sequence:**
1. Mentor tells the plain-language story of *why* the system is shaped this way (2–3 sentences per major decision) — before any diagram.
2. Provide a starter diagram with 1–2 deliberate omissions or errors.
3. Hunt: verify the diagram against reality; find and fix what's wrong or missing.
4. Contract cards: for each edge the learner touched, they write one card — "A promises B: ___; A assumes about B: ___; if B breaks, A does: ___".
5. Prediction test: "We're adding [plausible feature]. Which components change? Which don't? Why?"

**Question bank:**
- What does [component A] assume [component B] will never do? (A)
- Which arrows on this diagram are synchronous? What would break if one became async? (A)
- Where is the source of truth for [entity]? Who is allowed to write it? (A)
- Which boundary here exists for scale, and which for team ownership? (A)
- If you could delete one component, which one, and what absorbs its job?

**Anti-pattern to avoid:** presenting the finished, correct diagram first. A correct diagram gets nodded at and forgotten; a flawed one gets interrogated.

---

## 3. Concept

**Breakdown axis:** domain model in plain language *before* any implementation. Concepts fail to land when explanation, notation, and code arrive together.

**Sequence:**
1. Real-world analogy or story with no jargon (mentor supplies; test it by asking the learner to extend the analogy one step).
2. Vocabulary layer: map each analogy element to the formal term, one at a time.
3. Prediction questions before showing mechanism: "Given the story, what do you *think* happens when ___?"
4. Only now: the code/notation, with the learner narrating which part of the story each piece implements.
5. Transfer test: apply the concept to a second, structurally different example.

**Question bank:**
- In your own words, what problem existed before this concept? (A)
- What would go wrong if we did the naive thing instead? (A)
- Where in *our* codebase does this concept already appear, possibly unnamed? (A)
- What's the closest concept you already know, and where does the analogy break? 
- If the analogy is [X], what plays the role of [key element]? (A)

**Calibration note:** the transfer test (step 5) is the real checkpoint. Reciting the definition back is not understanding; applying it to an unfamiliar example is.

---

## 4. Task / Ticket

**Breakdown axis:** smallest end-to-end vertical slice. Struggling devs stall on tasks because the ticket bundles discovery, design, and implementation into one opaque blob.

**Sequence:**
1. Split the ticket into a **micro-deliverable ladder**: 3–6 rungs, each independently shippable or demoable, each touching the full stack thinly.
2. Rung 1 must be nearly trivial and visibly complete within a half-day — its job is momentum, not progress.
3. Before each rung, the learner states their approach in 2–3 sentences and gets a yes/adjust — not a design review, a nudge.
4. "Three before me" applies within rungs: bring three attempted hypotheses to any help request.
5. After the final rung: learner writes the "if I did this again" note — one paragraph, kept informal.

**Ladder example (feature: add export button to reports page):**
1. Button renders, does nothing → visible in UI
2. Button hits new endpoint returning hardcoded CSV → demoable end-to-end
3. Endpoint returns real data, one column → correctness surface appears
4. Full columns + edge cases (empty report, unicode) → real work
5. Loading/error states → polish

**Question bank:**
- What's the smallest version of this that someone could see working? (A)
- Which rung are you actually stuck on — is it smaller than the one you're describing?
- What are your three hypotheses, and how would you cheaply test each?
- What existing code does something 80% similar? (A)

---

## 5. Product

**Breakdown axis:** one user journey, experienced first as a user, then re-traced as a developer. Product understanding fails when devs meet the code before the *point* of the code.

**Sequence:**
1. Journey walk: learner completes one core user journey in the real product, taking notes as a *user* (what was confusing, slow, delightful).
2. Domain story: mentor explains who this user is and what they're trying to accomplish in their world — zero implementation talk.
3. Re-trace: learner maps each journey step to the code path that serves it (this becomes an Application-type hunt per step).
4. Break it: on a safe environment, break the journey at one step and observe what the user would experience — connects code failure to user pain.
5. Prediction: "Product wants to add [plausible change to the journey]. What's easy, what's hard, and why?"

**Question bank:**
- Who gets paged / who loses money when this journey breaks? (A)
- Which step of this journey is the business's actual moat? (A)
- Where does the product's language and the code's language disagree (UI says "project", code says "workspace")? (A)
- What does the user believe is happening at step [N] vs. what actually happens? (A)

---

## Cross-cutting: writing good guiding questions

A guiding question should be answerable by *looking*, not by *knowing*. "Why did we choose Kafka?" requires tribal knowledge — bad hunt question, fine debrief question. "Find where messages are consumed and what happens to failures" is answerable from the code — good hunt question. When drafting question banks, sort each question into hunt (answerable by exploration) vs. debrief (requires reflection or mentor context), and never put debrief questions inside the hunt itself.
