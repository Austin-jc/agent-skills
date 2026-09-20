#!/usr/bin/env python3
"""
check_output.py — deterministic gate for a Ticket Brief or Change Report.

Checks the generated markdown against the template and the writing rules:
required sections present and in order, no empty sections, no code or SQL,
no placeholder labels, no unexplained abbreviations, no filler words,
bullets not prose, and mode-specific content checks (a before/after walkthrough,
a why on every task, click paths on screen changes, and so on).

Exit code 0 = pass, 1 = errors. Fix every error, re-run, repeat until it passes.

Usage
  python3 check_output.py brief  .ticket-review/PROJ-123-brief.md
  python3 check_output.py report .ticket-review/PROJ-123-report.md
  python3 check_output.py report FILE --strict      # warnings count as errors
  python3 check_output.py report FILE --allow API,SDK   # abbreviations that are fine
  python3 check_output.py report FILE --json

Standard library only.
"""
import argparse
import json
import re
import sys

BRIEF_SECTIONS = [
    "At a glance", "Words you need to know", "Why this exists", "Before and after",
    "Scope and anti-scope", "Triggers, inputs, outputs, and failure", "The work involved",
    "What done looks like", "Assumptions, open questions, and what could break", "Self-check",
]
REPORT_SECTIONS = [
    "Summary, and asked versus built", "How it works, end to end", "User interface",
    "Endpoints and service interfaces", "Business rules and logic", "Data",
    "Configuration and flags", "Tests, and where to find everything",
    "Manual verification recipe, and what was not done", "Risk, watch list, and self-check",
]
# sections where a single "none" line is acceptable
OPTIONAL_REPORT = {"User interface", "Endpoints and service interfaces", "Business rules and logic", "Data", "Configuration and flags"}

CODE_FENCE_RX = re.compile(r"^\s*```")
SQL_RX = re.compile(r"\b(SELECT\b[\s\S]{0,80}\bFROM\b|INSERT\s+INTO\b|UPDATE\s+\w+\s+SET\b|DELETE\s+FROM\b|LEFT\s+JOIN\b|INNER\s+JOIN\b|JOIN\s+\w+\s+ON\b|GROUP\s+BY\b|ORDER\s+BY\b|WHERE\s+\w+\s*(=|<|>|IN\b)|CREATE\s+TABLE\b|ALTER\s+TABLE\b)", re.I)
CODEY_RX = re.compile(r"(=>|::|->|\(\);|\{\s*$|^\s*\}|\bconst\s+\w+\s*=|\blet\s+\w+\s*=|\bdef\s+\w+\(|\bfunction\s+\w+\(|\bfn\s+\w+\(|\bawait\s+\w+\.|\.then\(|\bnull\b|\bundefined\b|\btrue\b\s*[;,)]|\w+\.\w+\([^)]*\)\s*[;.]|\b\w+_\w+\(\))")
INLINE_CODE_RX = re.compile(r"`([^`]+)`")
PLACEHOLDER_RX = re.compile(r"\b(Option|Service|Step|Component|Module|Approach|Table|System|Endpoint|Screen|Query|Rule|Task|Feature|Method|Item)\s+[A-D]\b|\b[a-d][0-9]\b|\barg[0-9]\b|\bparam_[a-z]\b|\bfoo\b|\bbar\b|\bbaz\b|\bxyz\b|\bABC\b|\bTBD\b|\bTODO\b|\blorem\b|\[(amount|value|name|placeholder|insert[^\]]*)\]", re.I)
BANNED_WORDS_RX = re.compile(r"\b(robust|seamless(ly)?|leverag(e|es|ed|ing)|utiliz(e|es|ed|ing)|streamlin(e|es|ed|ing)|cutting[- ]edge|best[- ]in[- ]class|synerg\w+|holistic|paradigm|state[- ]of[- ]the[- ]art|elegant(ly)?|clean(ly)? and simple)\b", re.I)
ACRONYM_RX = re.compile(r"\b[A-Z][A-Z0-9]{1,6}s?\b")
TICKET_KEY_RX = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
HEDGE_RX = re.compile(r"\b(probably|(?<!most )(?<!least )likely|presumably|i think|i believe|seems to|appears to|might be|may be|perhaps|possibly)\b", re.I)
WHY_RX = re.compile(r"\b(because|needed|need(s)? this|so that|so the|so it|in order to|to allow|to make|to let|to stop|to prevent|to keep|to give|to avoid|to support|otherwise|which lets|which means|why:|reason:)\b", re.I)
CLICK_PATH_RX = re.compile(r"(\s>\s|→|\bthen\b.*\b(click|open|choose|select|tap|press|go to|navigate)|\b(click|open|choose|select|tap|press|log in|navigate|go to)\b.*\b(click|open|choose|select|tap|press|then|tab|menu|sidebar|button)\b)", re.I)
BEHAVIOR_RX = re.compile(r"behaviou?r\s+(is|was|remains)\s+(unchanged|the same|changed|different)|behaviou?r\s+(did not|does not|didn't|doesn't)\s+change|no\s+behaviou?r\s+change|changes?\s+(the\s+)?behaviou?r", re.I)
NONE_LINE_RX = re.compile(r"^\s*[-*]?\s*(no |none|nothing|not applicable|n/a|there (were|are) no|no (screen|endpoint|database|data|config|rule|logic)[^.]*(changed|added|removed|changes|work))", re.I)
BULLET_RX = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
HEADING_RX = re.compile(r"^\s*#{1,4}\s+(.*?)\s*$")


def strip_number(title):
    return re.sub(r"^\s*\d+[.)]?\s*", "", title).strip()


def norm(s):
    return re.sub(r"[^a-z]+", " ", s.lower()).strip()


def split_sections(lines):
    """Return list of (title, start_line, body_lines[(lineno, text)])."""
    sections, current = [], None
    for i, line in enumerate(lines, 1):
        m = HEADING_RX.match(line)
        if m and not line.strip().startswith("#####"):
            level = len(line) - len(line.lstrip("#").lstrip(" ")) - (len(line) - len(line.lstrip()))
            # accept ## or ### as section headings; # is the document title
            if line.lstrip().startswith("## ") or line.lstrip().startswith("### "):
                current = (strip_number(m.group(1)), i, [])
                sections.append(current)
                continue
            if line.lstrip().startswith("# "):
                continue
        if current is not None:
            current[2].append((i, line))
    return sections


def sentence_count(text):
    text = re.sub(r"\b(e\.g|i\.e|etc|vs|Mr|Mrs|Dr|No)\.", "", text)
    return len([s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip()) if s.strip()])


class Checker:
    def __init__(self, mode, allow):
        self.mode = mode
        # HTTP method names are names, not abbreviations; everything else must be spelled out
        self.allow = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} | {a.strip().upper() for a in allow if a.strip()}
        self.errors, self.warnings = [], []

    def err(self, line, msg):
        self.errors.append({"line": line, "message": msg})

    def warn(self, line, msg):
        self.warnings.append({"line": line, "message": msg})

    # ------------------------------------------------------------ structure
    def check_structure(self, sections):
        required = BRIEF_SECTIONS if self.mode == "brief" else REPORT_SECTIONS
        found = [norm(t) for t, _, _ in sections]
        req_norm = [norm(r) for r in required]
        positions = []
        for r, rn in zip(required, req_norm):
            idx = next((i for i, f in enumerate(found) if f.startswith(rn) or rn.startswith(f) and len(f) > 8), None)
            if idx is None:
                self.err(0, f"missing required section: \"{r}\"")
            else:
                positions.append(idx)
        if positions != sorted(positions):
            self.err(0, "sections are out of order — use the template order exactly")
        for t, ln, _ in sections:
            if norm(t) not in req_norm and not any(norm(t).startswith(rn) or rn.startswith(norm(t)) for rn in req_norm):
                self.warn(ln, f"unexpected section \"{t}\" — fold it into a template section or drop it")

    def check_section_bodies(self, sections):
        optional = OPTIONAL_REPORT if self.mode == "report" else set()
        for title, ln, body in sections:
            content = [(n, l) for n, l in body if l.strip()]
            if not content:
                self.err(ln, f"section \"{title}\" is empty")
                continue
            if len(content) == 1 and NONE_LINE_RX.match(content[0][1]):
                if title not in optional and not any(norm(title).startswith(norm(o)) for o in optional):
                    self.err(ln, f"section \"{title}\" is just a 'none' line — this section always needs real content")
                continue
            bullets = [l for _, l in content if BULLET_RX.match(l)]
            prose = [l for _, l in content if not BULLET_RX.match(l) and not l.strip().startswith(("**", "#"))]
            if len(content) >= 3 and len(prose) > len(content) * 0.5:
                self.warn(ln, f"section \"{title}\" is mostly prose ({len(prose)} paragraph lines vs {len(bullets)} bullets) — use bullets")
            for n, l in content:
                if BULLET_RX.match(l):
                    text = BULLET_RX.sub("", l)
                    sc = sentence_count(text)
                    if sc > 4:
                        self.err(n, f"bullet has {sc} sentences — split it (three is the ceiling)")
                    elif sc == 4:
                        self.warn(n, "bullet has four sentences — split it")

    # ------------------------------------------------------------ language
    def check_language(self, lines):
        in_fence = False
        spelled = set()
        for n, line in enumerate(lines, 1):
            if CODE_FENCE_RX.match(line):
                if not in_fence:
                    self.err(n, "code fence — describe what the code does instead of pasting it")
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if SQL_RX.search(line):
                self.err(n, "looks like SQL — describe the query conceptually (what it joins, filters, sorts, returns)")
            for m in INLINE_CODE_RX.finditer(line):
                inner = m.group(1)
                if "(" in inner or "=" in inner or len(inner) > 60:
                    self.err(n, f"inline code `{inner[:40]}` — file paths and names are fine in backticks, expressions are not")
            if CODEY_RX.search(line) and not INLINE_CODE_RX.search(line):
                self.warn(n, "line looks like code syntax — rewrite in plain words")
            m = PLACEHOLDER_RX.search(line)
            if m:
                self.err(n, f"placeholder label \"{m.group(0)}\" — use the real name")
            m = BANNED_WORDS_RX.search(line)
            if m:
                self.err(n, f"filler word \"{m.group(0)}\" — say what actually happens")
            if HEDGE_RX.search(line) and not re.search(r"assum|confirm|not stated|unknown|unclear|question", line, re.I):
                self.warn(n, "hedged claim — either state it as an assumption to confirm, or state it plainly")
            # abbreviations: allow if spelled out earlier as "Long Form (ABBR)" or in the allow list
            for pm in re.finditer(r"\(([A-Z][A-Z0-9]{1,6})\)", line):
                spelled.add(pm.group(1))
            for am in ACRONYM_RX.finditer(line):
                tok = am.group(0).rstrip("s")
                if re.match(r"-\d", line[am.end():]):  # part of a ticket key like BILL-470
                    continue
                if tok in self.allow or tok in spelled or TICKET_KEY_RX.match(tok) or len(tok) < 2:
                    continue
                # skip things inside backticks (file names, env keys) and headings
                inside_code = any(m.start() <= am.start() < m.end() for m in INLINE_CODE_RX.finditer(line))
                if inside_code or line.lstrip().startswith("#"):
                    continue
                if tok in ("I", "A", "OK", "US", "UK"):
                    continue
                self.err(n, f"abbreviation \"{tok}\" not spelled out — write the full term first, e.g. \"Full Term ({tok})\", or pass --allow {tok}")

    # ------------------------------------------------------------ mode-specific
    def section(self, sections, name):
        for t, ln, body in sections:
            if norm(t).startswith(norm(name)) or norm(name).startswith(norm(t)) and len(norm(t)) > 8:
                return ln, [(n, l) for n, l in body if l.strip()]
        return None, []

    def check_brief(self, sections):
        ln, body = self.section(sections, "Before and after")
        if body:
            text = "\n".join(l for _, l in body)
            if not re.search(r"\bbefore\b", text, re.I) or not re.search(r"\bafter\b", text, re.I):
                self.err(ln, "walkthrough must have a clearly marked Before part and After part")
            if re.search(r"\b(a|the) user\b", text, re.I):
                self.err(ln, "walkthrough says \"the user\" — name the actual role (billing specialist, purchasing coordinator, support agent)")
            if not re.search(r"\b(step|click|open|receive|see|check|run|log in|submit|enter|export|send|review|approve)", text, re.I):
                self.warn(ln, "walkthrough does not read like a step-by-step story — describe what the person actually does")
        ln, body = self.section(sections, "Scope and anti-scope")
        if body and not re.search(r"(must not|not change|leave alone|do not touch|not touch|untouched|preserve|out of scope|excluded|unchanged)", "\n".join(l for _, l in body), re.I):
            self.err(ln, "anti-scope missing — name the existing behaviour and adjacent screens or endpoints that must not change")
        ln, body = self.section(sections, "The work involved")
        if body:
            tasks = [(n, l) for n, l in body if BULLET_RX.match(l) and not re.match(r"^\s{2,}", l)
                     and not re.match(r"^\s*[-*]\s*\**(uncertain|risky|risk|choice|open|note|order|decision)", l, re.I)]
            if len(tasks) < 2:
                self.err(ln, "task list has fewer than two tasks — list the actual work in order")
            for n, l in tasks:
                if not WHY_RX.search(l):
                    self.err(n, "task has no stated reason — add why it is needed (\"because\", \"so that\", \"needed to\")")
                if not re.search(r"`[^`]+`|\b(in|lives in|inside|under)\s+(the\s+)?[\w./-]+", l):
                    self.warn(n, "task does not say which part of the system it lives in")
        ln, body = self.section(sections, "Triggers, inputs")
        if body:
            text = "\n".join(l for _, l in body)
            for word in ("trigger", "input", "output", "fail"):
                if not re.search(r"\b" + word, text, re.I):
                    self.err(ln, f"inputs/outputs section does not cover {word}s")
            if re.search(r"\b(string|integer|int|uuid|boolean|bool|json|float|varchar|payload)\b", text, re.I):
                self.warn(ln, "inputs described as data types — describe them as business data (\"the customer's email address\")")
        ln, body = self.section(sections, "Assumptions")
        if body and not re.search(r"assum", "\n".join(l for _, l in body), re.I):
            self.err(ln, "no assumptions listed — every brief has assumptions; find them and flag them for confirmation")
        ln, body = self.section(sections, "Why this exists")
        if body:
            text = "\n".join(l for _, l in body)
            if not re.search(r"\b(cost|lose|loses|lost|wast|risk|delay|hours|minutes|days|money|revenue|errors?|complaints?|escalat|if (we|this is|nothing)|do nothing|inaction)", text, re.I):
                self.err(ln, "business reason does not state the cost of the problem or the cost of doing nothing")
            if not re.search(r"\b(team|specialist|coordinator|manager|agent|analyst|engineer|customer|client|operator|admin|accountant|staff|department|finance|billing|support|sales|ops)\b", text, re.I):
                self.warn(ln, "business reason does not name a real role or team")
            if re.search(r"\b(a|the) user\b", text, re.I):
                self.warn(ln, "\"the user\" — name the actual role")

    def check_report(self, sections):
        ln, body = self.section(sections, "Summary")
        if body and not re.search(r"\b(delivered|fully|partly|partially|not at all|not delivered|not done|as asked|matches)\b", "\n".join(l for _, l in body), re.I):
            self.err(ln, "summary must compare asked versus built — say for each scope item whether it was delivered fully, partly, or not at all")
        ln, body = self.section(sections, "How it works")
        if body:
            bullets = [l for _, l in body if BULLET_RX.match(l)]
            if len(bullets) < 3:
                self.err(ln, "end-to-end flow has fewer than three steps — trace every hop from trigger to result")
            text = "\n".join(l for _, l in body)
            if not re.search(r"\b(when|clicks?|opens?|submits?|runs?|receives?|sends?|calls?|returns?|saves?|checks?|asks?)\b", text, re.I):
                self.warn(ln, "flow does not read like a story of what happens — start each step with the actor and the action")
        ln, body = self.section(sections, "User interface")
        if body and not (len(body) == 1 and NONE_LINE_RX.match(body[0][1])):
            text = "\n".join(l for _, l in body)
            if not CLICK_PATH_RX.search(text):
                self.err(ln, "screen change without a click path — give the exact route from the starting page (\"Log in, open Reports, choose the Clients tab, then …\")")
            if not re.search(r"\bbefore\b", text, re.I):
                self.err(ln, "screen change without a before-versus-after — say what was there previously")
            if not re.search(r"\b(loading|empty|no data|error|fails?|disabled|greyed|hidden|only (appears|shows|visible)|for (admin|manager|role))", text, re.I):
                self.warn(ln, "no loading / empty / error / conditional states described for the screen change")
        ln, body = self.section(sections, "Business rules")
        if body:
            text = "\n".join(l for _, l in body)
            if re.search(r"refactor|moved|renamed|split|merged|restructur|extract", text, re.I) and not BEHAVIOR_RX.search(text):
                self.err(ln, "refactoring mentioned without an explicit statement of whether behaviour changed")
        ln, body = self.section(sections, "Data")
        if body and not (len(body) == 1 and NONE_LINE_RX.match(body[0][1])):
            text = "\n".join(l for _, l in body)
            if re.search(r"\bquer(y|ies)\b", text, re.I) and not re.search(r"\b(join|link|connect|filter|only|where|limit|sort|order|rank|total|sum|count|group|return)", text, re.I):
                self.err(ln, "query described too vaguely — say what it links, filters on, sorts by, and returns")
        ln, body = self.section(sections, "Tests")
        if body:
            text = "\n".join(l for _, l in body)
            if not re.search(r"`[^`]+`", text):
                self.err(ln, "file map missing — list every changed file in backticks with one line on what it does")
            if not re.search(r"\b(test|prove|confirm|check|cover)", text, re.I):
                self.err(ln, "no tests described — say what each test proves, or state that none were added and what needs a manual check")
        ln, body = self.section(sections, "Manual verification")
        if body:
            text = "\n".join(l for _, l in body)
            if not re.search(r"^\s*\d+[.)]\s", text, re.M):
                self.err(ln, "verification recipe must be numbered steps")
            if not re.search(r"\b(should see|expect|correct result|looks like|confirm|shows|appears|displays)\b", text, re.I):
                self.err(ln, "recipe does not say what a correct result looks like")
            if not re.search(r"\b(fail|error|blank|empty|invalid|double|down|missing|edge)", text, re.I):
                self.err(ln, "recipe has no failure or edge case step")
            if not re.search(r"\b(not done|left out|deferred|follow[- ]up|rough edge|shortcut|out of scope|nothing was left)", text, re.I):
                self.warn(ln, "say explicitly what was not done, or that nothing was left out")
        ln, body = self.section(sections, "Risk")
        if body:
            text = "\n".join(l for _, l in body)
            if not re.search(r"\b(from the diff|against the diff|based on the diff|diff)\b", text, re.I):
                self.warn(ln, "self-check should confirm the report was written from the diff")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["brief", "report"])
    ap.add_argument("file")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--allow", default="", help="comma-separated abbreviations that need no spelling out")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()

    c = Checker(args.mode, args.allow.split(","))
    sections = split_sections(lines)
    if not sections:
        c.err(0, "no sections found — use '## 1. Section name' headings exactly as in the template")
    else:
        c.check_structure(sections)
        c.check_section_bodies(sections)
        (c.check_brief if args.mode == "brief" else c.check_report)(sections)
    c.check_language(lines)

    errors = c.errors + (c.warnings if args.strict else [])
    warnings = [] if args.strict else c.warnings
    errors.sort(key=lambda e: e["line"])
    warnings.sort(key=lambda e: e["line"])

    if args.json:
        print(json.dumps({"pass": not errors, "errors": errors, "warnings": warnings}, indent=1))
    else:
        if errors:
            print(f"FAIL — {len(errors)} error(s) in {args.file}")
            for e in errors:
                print(f"  line {e['line']:>4}: {e['message']}")
        else:
            print(f"PASS — {args.file} meets the {args.mode} template")
        if warnings:
            print(f"\n{len(warnings)} warning(s):")
            for w in warnings:
                print(f"  line {w['line']:>4}: {w['message']}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
