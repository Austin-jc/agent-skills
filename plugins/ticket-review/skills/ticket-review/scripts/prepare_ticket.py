#!/usr/bin/env python3
"""
prepare_ticket.py — deterministic pre-phase for the Ticket Brief.

Takes a ticket from a file, standard input, or Jira, and produces:
  .ticket-review/ticket.md            compact normalized ticket (title, type, parent,
                                      links, description, acceptance criteria, comments)
  .ticket-review/glossary-candidates.md  terms that probably need defining
  .ticket-review/candidate-files.md   files in the repo that mention those terms,
                                      ranked, with their area — so Claude reads only these

Usage
  python3 prepare_ticket.py --file ticket.md
  cat ticket.txt | python3 prepare_ticket.py
  python3 prepare_ticket.py --jira PROJ-123        # needs JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN
  python3 prepare_ticket.py --file ticket.md --no-locate   # skip repo search

Standard library only. Jira fetch uses urllib; nothing else leaves the machine.
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_common import classify, ensure_out_dir, is_noise, repo_root, run, truncate  # noqa: E402

STOPWORDS = set("""
a an the and or but if then else when while for to of in on at by with from into onto over under about after before
between during without within through across against along around above below up down out off this that these those
it its is are was were be been being have has had do does did will would shall should can could may might must
not no nor so than too very just also only same such each every either neither both all any some more most other
another own new old first last next which who whom whose what where why how here there now ever never always often
we you they he she i me him her us them our your their my his mine yours theirs ours ticket issue story task bug
feature request please need needs needed should would like want wants make sure ensure add added adding update
updated updating change changed changing fix fixed fixing implement implemented implementation currently current
user users use used using able unable via per etc eg ie example following above below see note notes description
acceptance criteria given when then and/or done todo wip
""".split())

ACCEPTANCE_HEADING_RX = re.compile(r"^\s*#*\s*(acceptance\s+criteria|acceptance|definition\s+of\s+done|dod|success\s+criteria|expected\s+(behaviou?r|result))\b.*$", re.I)
GWT_RX = re.compile(r"^\s*[-*]?\s*(given|when|then|and)\b", re.I)


# ---------------------------------------------------------------- Jira


def jira_get(base, email, token, path):
    req = urllib.request.Request(base.rstrip("/") + path)
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def adf_to_text(node):
    """Flatten Atlassian Document Format (or plain string) to text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(adf_to_text(n) for n in node)
    t = node.get("type")
    if t == "text":
        return node.get("text", "")
    if t == "hardBreak":
        return "\n"
    if t == "mention":
        return "@" + node.get("attrs", {}).get("text", "someone")
    inner = adf_to_text(node.get("content", []))
    if t in ("paragraph", "heading"):
        prefix = "#" * node.get("attrs", {}).get("level", 0) + " " if t == "heading" else ""
        return prefix + inner + "\n"
    if t == "listItem":
        return "- " + inner
    if t in ("bulletList", "orderedList", "blockquote", "codeBlock", "table", "tableRow", "panel"):
        return inner + ("\n" if t != "tableRow" else "")
    if t == "tableCell" or t == "tableHeader":
        return inner.strip() + " | "
    return inner


def fetch_jira(key):
    base, email, token = (os.environ.get(k) for k in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"))
    if not all((base, email, token)):
        sys.exit("Jira fetch needs JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in the environment")
    fields = "summary,description,issuetype,status,priority,labels,components,parent,issuelinks,comment,created,reporter"
    try:
        issue = jira_get(base, email, token, f"/rest/api/3/issue/{key}?fields={fields}")
    except urllib.error.HTTPError as e:
        sys.exit(f"Jira returned {e.code} for {key}: {e.read().decode()[:300]}")
    f = issue["fields"]
    ticket = {
        "key": issue["key"],
        "title": f.get("summary", ""),
        "type": (f.get("issuetype") or {}).get("name", ""),
        "status": (f.get("status") or {}).get("name", ""),
        "priority": (f.get("priority") or {}).get("name", ""),
        "labels": f.get("labels") or [],
        "components": [c.get("name") for c in f.get("components") or []],
        "reporter": ((f.get("reporter") or {}).get("displayName") or ""),
        "description": adf_to_text(f.get("description")),
        "parent": None,
        "links": [],
        "comments": [],
        "url": base.rstrip("/") + "/browse/" + issue["key"],
    }
    parent = f.get("parent")
    if parent:
        try:
            p = jira_get(base, email, token, f"/rest/api/3/issue/{parent['key']}?fields=summary,description,issuetype")
            ticket["parent"] = {"key": p["key"], "title": p["fields"].get("summary", ""),
                                "type": (p["fields"].get("issuetype") or {}).get("name", ""),
                                "description": truncate(adf_to_text(p["fields"].get("description")), 900)}
        except Exception:
            ticket["parent"] = {"key": parent["key"], "title": parent.get("fields", {}).get("summary", ""), "type": "", "description": ""}
    for link in f.get("issuelinks") or []:
        other = link.get("outwardIssue") or link.get("inwardIssue")
        rel = link.get("type", {}).get("outward" if "outwardIssue" in link else "inward", "related to")
        if other:
            ticket["links"].append({"key": other["key"], "title": other.get("fields", {}).get("summary", ""), "relation": rel})
    for c in (f.get("comment") or {}).get("comments", [])[-10:]:
        ticket["comments"].append({"author": (c.get("author") or {}).get("displayName", "someone"),
                                   "date": (c.get("created") or "")[:10], "text": adf_to_text(c.get("body"))})
    return ticket


# ---------------------------------------------------------------- plain text / file input


def parse_plain(text, key_hint=None):
    lines = text.splitlines()
    title = ""
    for l in lines:
        if l.strip():
            title = l.strip().lstrip("# ").strip()
            break
    m = re.search(r"\b([A-Z][A-Z0-9]+-\d+)\b", text)
    key = key_hint or (m.group(1) if m else "")
    if key and title.startswith(key):
        title = title[len(key):].lstrip(" :—-–").strip()
    # drop the title line from the body so it is not repeated
    body_lines = lines[:]
    for i, l in enumerate(body_lines):
        if l.strip():
            body_lines.pop(i)
            break
    text = "\n".join(body_lines).strip()
    return {"key": key, "title": title, "type": "", "status": "", "priority": "", "labels": [], "components": [],
            "reporter": "", "description": text, "parent": None, "links": [], "comments": [], "url": ""}


def load_input(args):
    if args.jira:
        return fetch_jira(args.jira)
    if args.file:
        with open(args.file, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        if args.file.lower().endswith(".json"):
            try:
                data = json.loads(raw)
                if "fields" in data:  # raw Jira export
                    f = data["fields"]
                    return {"key": data.get("key", ""), "title": f.get("summary", ""), "type": (f.get("issuetype") or {}).get("name", ""),
                            "status": (f.get("status") or {}).get("name", ""), "priority": (f.get("priority") or {}).get("name", ""),
                            "labels": f.get("labels") or [], "components": [], "reporter": "", "description": adf_to_text(f.get("description")),
                            "parent": None, "links": [], "comments": [{"author": (c.get("author") or {}).get("displayName", ""), "date": (c.get("created") or "")[:10], "text": adf_to_text(c.get("body"))} for c in (f.get("comment") or {}).get("comments", [])], "url": ""}
                return {**parse_plain(data.get("description", ""), data.get("key")), "title": data.get("title", "") or data.get("summary", "")}
            except json.JSONDecodeError:
                pass
        return parse_plain(raw)
    if not sys.stdin.isatty():
        return parse_plain(sys.stdin.read())
    sys.exit("give me a ticket: --file PATH, --jira KEY, or text on standard input")


# ---------------------------------------------------------------- normalization


def split_acceptance(description):
    """Pull an acceptance-criteria block out of the description if one exists."""
    lines = description.splitlines()
    body, ac, in_ac = [], [], False
    for l in lines:
        if ACCEPTANCE_HEADING_RX.match(l):
            in_ac = True
            continue
        if in_ac and re.match(r"^\s*#+\s", l):  # next heading ends the block
            in_ac = False
        (ac if in_ac else body).append(l)
    if not ac:
        gwt = [l for l in lines if GWT_RX.match(l)]
        if len(gwt) >= 2:
            ac = gwt
            body = [l for l in lines if l not in gwt]
    return "\n".join(body).strip(), "\n".join(ac).strip()


def glossary_candidates(text, key="", title=""):
    cands = Counter()
    key_prefix = key.split("-")[0].lower() if key else ""
    title_first = title.split()[0].lower() if title else ""
    for m in re.finditer(r"[\"“']([A-Za-z][A-Za-z0-9 \-/]{2,40})[\"”']", text):
        cands[m.group(1).strip()] += 2
    for m in re.finditer(r"`([^`\n]{2,40})`", text):
        cands[m.group(1).strip()] += 2
    for m in re.finditer(r"\b([A-Z][A-Z0-9]{1,7})\b", text):
        if not re.match(r"^[A-Z]+-\d+$", m.group(1)):
            cands[m.group(1)] += 1
    # Capitalized phrases not at the start of a sentence
    for m in re.finditer(r"(?<![.!?\n]\s)(?<!^)\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", text):
        phrase = m.group(1)
        if phrase.lower() not in STOPWORDS and len(phrase) > 3:
            cands[phrase] += 1
    # Frequent domain words
    words = re.findall(r"\b[a-z][a-z_\-]{4,}\b", text.lower())
    for w, n in Counter(words).items():
        if n >= 2 and w not in STOPWORDS:
            cands[w] += n - 1
    def junk(t):
        tl = t.lower().rstrip("-")
        return (not tl) or tl == key_prefix or tl == title_first or tl in STOPWORDS or t.endswith("-")
    ranked = [t for t, _ in cands.most_common(60) if not junk(t)]
    # drop near-duplicates (case-insensitive)
    seen, out = set(), []
    for t in ranked:
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out[:25]


def locate_files(root, terms, limit=25):
    """git grep each term; rank files by distinct terms matched, then total matches."""
    hits = defaultdict(lambda: {"terms": set(), "count": 0})
    for term in terms:
        if len(term) < 4:
            continue
        out = run(["git", "grep", "-i", "-c", "--", term], cwd=root, check=False)
        for line in out.splitlines():
            path, _, n = line.rpartition(":")
            if not path or is_noise(path) or classify(path) in ("docs",):
                continue
            hits[path]["terms"].add(term)
            hits[path]["count"] += int(n or 0)
    ranked = sorted(hits.items(), key=lambda kv: (-len(kv[1]["terms"]), -kv[1]["count"], kv[0]))
    return [(p, sorted(v["terms"]), v["count"], classify(p)) for p, v in ranked[:limit]]


def render_ticket(t):
    body, ac = split_acceptance(t["description"])
    out = [f"# {t['key'] + ' — ' if t['key'] else ''}{t['title']}"]
    meta = [("Type", t["type"]), ("Status", t["status"]), ("Priority", t["priority"]),
            ("Labels", ", ".join(t["labels"])), ("Components", ", ".join(t["components"])), ("Reporter", t["reporter"]), ("Link", t["url"])]
    meta = [f"- {k}: {v}" for k, v in meta if v]
    if meta:
        out.extend(meta)
    if t["parent"]:
        p = t["parent"]
        out.append(f"\n## Parent / epic: {p['key']} — {p['title']}" + (f" ({p['type']})" if p.get("type") else ""))
        if p.get("description"):
            out.append(p["description"])
    if t["links"]:
        out.append("\n## Linked issues")
        out.extend(f"- {l['relation']}: {l['key']} — {l['title']}" for l in t["links"])
    out.append("\n## Description")
    out.append(truncate(body, 6000) if body else "(empty)")
    out.append("\n## Acceptance criteria")
    out.append(ac if ac else "(none found in the ticket — the brief must say so)")
    if t["comments"]:
        out.append(f"\n## Comments (latest {len(t['comments'])})")
        for c in t["comments"]:
            out.append(f"- **{c['author']}** {c['date']}: {truncate(c['text'], 600)}")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="ticket as .md, .txt or .json (Jira export or {title, description})")
    ap.add_argument("--jira", metavar="KEY", help="fetch from Jira using JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN")
    ap.add_argument("--repo", help="path inside the repository (default: cwd)")
    ap.add_argument("--out", default=".ticket-review")
    ap.add_argument("--no-locate", action="store_true", help="skip searching the repo for candidate files")
    ap.add_argument("--limit", type=int, default=25, help="max candidate files")
    args = ap.parse_args()

    ticket = load_input(args)
    root = repo_root(args.repo) or os.getcwd()
    out_dir = ensure_out_dir(root, args.out)

    ticket_md = render_ticket(ticket)
    with open(os.path.join(out_dir, "ticket.md"), "w", encoding="utf-8") as fh:
        fh.write(ticket_md)
    with open(os.path.join(out_dir, "ticket.json"), "w", encoding="utf-8") as fh:
        json.dump(ticket, fh, indent=1)

    full_text = "\n".join([ticket["title"], ticket["description"]] + [c["text"] for c in ticket["comments"]] + ([ticket["parent"]["description"]] if ticket["parent"] else []))
    terms = glossary_candidates(full_text, ticket["key"], ticket["title"])
    gl = ["# Glossary candidates", "Terms that appear important in the ticket. Define each one in the brief's section two, or state that it is generic.", ""]
    gl.extend(f"- {t}" for t in terms)
    with open(os.path.join(out_dir, "glossary-candidates.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(gl) + "\n")

    cand_md = ["# Candidate files", "Files in this repository that mention the ticket's terms, ranked by how many distinct terms they match.",
               "Read the top few in each area before writing the brief. Do not read files outside this list unless one of these points at them.", ""]
    if not args.no_locate and repo_root(args.repo):
        cands = locate_files(root, terms, args.limit)
        if cands:
            by_area = defaultdict(list)
            for p, ts, n, area in cands:
                by_area[area].append((p, ts, n))
            for area in ("screens", "api", "services", "database", "migrations", "config", "tests", "other"):
                if area in by_area:
                    cand_md.append(f"\n## {area}")
                    for p, ts, n in by_area[area]:
                        cand_md.append(f"- `{p}` — {n} matches on: {', '.join(ts[:6])}")
        else:
            cand_md.append("(no files matched — the ticket's vocabulary may not match the code's; ask the reader where this lives)")
    else:
        cand_md.append("(repository search skipped)")
    with open(os.path.join(out_dir, "candidate-files.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(cand_md) + "\n")

    print(ticket_md)
    print("\n".join(gl))
    print()
    print("\n".join(cand_md))


if __name__ == "__main__":
    main()
