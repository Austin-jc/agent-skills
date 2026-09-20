#!/usr/bin/env python3
"""
inventory_diff.py — deterministic pre-phase for the Change Report.

Reads the git diff between a base ref and HEAD (or the working tree) and
produces a compact, classified inventory: which files changed in which
area, which endpoints / queries / schema / config keys / tests / functions
were added or removed, and the commit messages. The point is that Claude
reads this summary (a few hundred tokens) instead of the raw diff, then
pulls only the hunks it actually needs with --hunk.

Usage
  python3 inventory_diff.py                      # auto-detect base, print inventory.md
  python3 inventory_diff.py --base origin/main   # explicit base
  python3 inventory_diff.py --working-tree       # include uncommitted changes
  python3 inventory_diff.py --hunk src/api/checkout.py [--max-lines 200]
  python3 inventory_diff.py --json               # print inventory.json instead

Writes .ticket-review/inventory.json, inventory.md and diff.patch in the repo.
Standard library only.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_common import AREA_ORDER, classify, ensure_out_dir, is_noise, repo_root, run, truncate  # noqa: E402

# ---------------------------------------------------------------- signal regexes
ROUTE_PATTERNS = [
    # Flask / FastAPI / Express / Koa / Hono style
    re.compile(r"@?\b(?:app|router|api|bp|blueprint|route[rs]?)\.(get|post|put|patch|delete|options|head|all)\(\s*['\"]([^'\"]+)", re.I),
    # NestJS / Spring style decorators
    re.compile(r"@(Get|Post|Put|Patch|Delete|GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\(\s*['\"]?([^'\")]*)"),
    # Rust actix / rocket / axum
    re.compile(r"#\[(get|post|put|patch|delete)\(\s*\"([^\"]+)\""),
    re.compile(r"\.route\(\s*['\"]([^'\"]+)['\"]\s*,\s*(get|post|put|patch|delete)\("),
    # Go net/http, gin, chi, echo
    re.compile(r"\.(HandleFunc|Handle|GET|POST|PUT|PATCH|DELETE)\(\s*\"([^\"]+)\""),
    # Django / Django REST
    re.compile(r"\b(path|re_path|url)\(\s*['\"]([^'\"]+)"),
    # Generic "METHOD /path" strings, e.g. in OpenAPI or comments
    re.compile(r"['\"](GET|POST|PUT|PATCH|DELETE)\s+(/[^'\"\s]+)"),
]

SQL_RX = re.compile(r"\b(SELECT\b.*\bFROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|WITH\s+\w+\s+AS|MERGE\s+INTO)\b", re.I)
ORM_RX = re.compile(r"\.(filter|filter_by|where|whereIn|join|leftJoin|innerJoin|select|order_by|orderBy|group_by|groupBy|findMany|findFirst|findUnique|aggregate|having|distinct|raw|rawQuery|query|execute|exec|fetch_all|fetch_one|scalars)\(|\bprisma\.\w+\.\w+\(|\bsqlx::query|\bdiesel::|\bknex\(|\bdb\.(query|execute|select|insert|update|delete)\(|session\.(query|execute)\(|\bselect\(|\bsql`|\bSQL\(")
SCHEMA_RX = re.compile(r"\b(CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE|ADD\s+COLUMN|DROP\s+COLUMN|RENAME\s+COLUMN|CREATE\s+(UNIQUE\s+)?INDEX|DROP\s+INDEX|create_table|add_column|remove_column|drop_column|rename_column|add_index|create_index|addColumn|dropColumn|createTable|dropTable|createIndex|op\.(create_table|add_column|drop_column|alter_column|create_index)|\.integer\(|\.string\(|\.timestamp\()|^\s*model\s+\w+\s*\{|@@index|@@unique|#\[derive\(.*(Queryable|Insertable)", re.I | re.M)
ENV_RX = re.compile(r"process\.env\.(\w+)|os\.environ(?:\.get)?\(\s*['\"](\w+)|os\.getenv\(\s*['\"](\w+)|env::var\(\s*\"(\w+)|getenv\(\s*\"(\w+)|Deno\.env\.get\(\s*['\"](\w+)|import\.meta\.env\.(\w+)|settings\.([A-Z][A-Z0-9_]+)\b|config\.(?:get\()?['\"]?([A-Z][A-Z0-9_]{3,})")
FLAG_RX = re.compile(r"(feature[_-]?flag|is[_-]?enabled|isFeatureEnabled|launchdarkly|ldclient|unleash|flagsmith|useFlag|getFlag|flags?\.\w+\.enabled|FEATURE_[A-Z_]+)", re.I)
FUNC_RX = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:pub(?:\([^)]*\))?\s+)?(?:def|function|fn|func)\s+([A-Za-z_]\w*)")
CLASS_RX = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:pub\s+)?(?:class|struct|enum|interface|trait|type)\s+([A-Za-z_]\w*)")
COMPONENT_RX = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:const|function)\s+([A-Z][A-Za-z0-9]*)\s*(?:=|\()")
TEST_RX = re.compile(r"^\s*(?:def\s+(test_\w+)|(?:it|test|describe)\(\s*['\"`]([^'\"`]+)|#\[test\]|func\s+(Test\w+)\()")
JSX_TEXT_RX = re.compile(r">\s*([A-Z][^<>{}]{8,120}?)\s*<")
UI_STRING_RX = re.compile(r"(?:label|title|placeholder|aria-label|buttonText|message|heading|tooltip|text)\s*[=:]\s*['\"`]([^'\"`]{4,120})['\"`]")
UI_ROUTE_RX = re.compile(r"(?:path\s*[:=]\s*['\"]|<Route[^>]*path=['\"]|href=['\"]|to=['\"]|navigate\(\s*['\"]|router\.push\(\s*['\"])(/[^'\"\s]*)")
VALIDATION_RX = re.compile(r"\b(raise|throw)\b|\bValidationError\b|\bBadRequest\b|\bHttpException\b|status(?:_code)?\s*[:=]\s*4\d\d|\bassert\b|\.isRequired|\brequired\s*:\s*true|\bz\.(string|number|object)|\bjoi\.|\byup\.", re.I)
STATE_RX = re.compile(r"\b(status|state)\s*(?:=|==|===|!=|:)\s*['\"]?[A-Z_a-z]+['\"]?|\bset(Status|State)\(|transition|\.status\s*=", re.I)

# ---------------------------------------------------------------- diff parsing


def parse_diff(patch):
    """Yield (path, old_path, status, added_lines, removed_lines, hunk_text) per file."""
    files = []
    current = None
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            if current:
                files.append(current)
            m = re.match(r"diff --git a/(.*?) b/(.*)$", line)
            new_path = m.group(2) if m else line[11:]
            old_path = m.group(1) if m else new_path
            current = {"path": new_path, "old_path": old_path, "status": "modified", "added": [], "removed": [], "hunk": [line], "binary": False, "context": []}
            continue
        if current is None:
            continue
        current["hunk"].append(line)
        if line.startswith("@@"):
            ctx = line.split("@@")[-1].strip()
            if ctx:
                current["context"].append(ctx)
        if line.startswith("new file mode"):
            current["status"] = "added"
        elif line.startswith("deleted file mode"):
            current["status"] = "deleted"
        elif line.startswith("rename from"):
            current["status"] = "renamed"
        elif line.startswith("Binary files"):
            current["binary"] = True
        elif line.startswith("+") and not line.startswith("+++"):
            current["added"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current["removed"].append(line[1:])
    if current:
        files.append(current)
    return files


def touched_context(ctx_lines):
    """Names of functions/classes whose body was edited, from git hunk headers."""
    out = []
    for c in ctx_lines:
        m = re.search(r"(?:def|function|fn|func|class|struct|impl|const|export\s+(?:default\s+)?(?:function|const))\s+([A-Za-z_][\w.]*)", c)
        name = m.group(1) if m else truncate(c, 60)
        if name and name not in out:
            out.append(name)
    return out


def first_group(m):
    return next((g for g in m.groups() if g), "")


def extract_signals(lines, path):
    """Return a dict of signal lists found in a list of source lines."""
    s = {"routes": [], "sql": [], "orm": [], "schema": [], "env": [], "flags": [], "functions": [],
         "classes": [], "components": [], "tests": [], "ui_text": [], "ui_routes": [], "validation": [], "state": []}
    is_ui = bool(re.search(r"\.(tsx|jsx|vue|svelte|html)$", path, re.I))
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith(("//", "#", "*", "/*")) and not stripped.startswith("#["):
            # skip pure comment lines (but keep Rust attributes like #[get(...)])
            if not stripped.startswith("#["):
                continue
        for rx in ROUTE_PATTERNS:
            m = rx.search(line)
            if m:
                groups = [g for g in m.groups() if g]
                if len(groups) >= 2:
                    method, route = (groups[0], groups[1]) if groups[0].isalpha() and len(groups[0]) <= 14 else (groups[1], groups[0])
                    s["routes"].append(f"{method.upper()} {route}")
                elif groups:
                    s["routes"].append(groups[0])
                break
        if SQL_RX.search(line):
            s["sql"].append(truncate(stripped, 160))
        elif ORM_RX.search(line):
            s["orm"].append(truncate(stripped, 160))
        if SCHEMA_RX.search(line):
            s["schema"].append(truncate(stripped, 160))
        for m in ENV_RX.finditer(line):
            s["env"].append(first_group(m))
        if FLAG_RX.search(line):
            s["flags"].append(truncate(stripped, 160))
        m = FUNC_RX.match(line)
        if m:
            s["functions"].append(m.group(1))
        m = CLASS_RX.match(line)
        if m:
            s["classes"].append(m.group(1))
        m = TEST_RX.match(line)
        if m:
            name = first_group(m) or "(#[test])"
            s["tests"].append(name)
        if is_ui:
            m = COMPONENT_RX.match(line)
            if m and m.group(1) not in s["components"]:
                s["components"].append(m.group(1))
            for m in JSX_TEXT_RX.finditer(line):
                s["ui_text"].append(truncate(m.group(1), 120))
            for m in UI_STRING_RX.finditer(line):
                s["ui_text"].append(truncate(m.group(1), 120))
        for m in UI_ROUTE_RX.finditer(line):
            s["ui_routes"].append(m.group(1))
        if VALIDATION_RX.search(line) and not stripped.startswith(("import", "from", "use ")):
            s["validation"].append(truncate(stripped, 160))
        if STATE_RX.search(line) and "import" not in stripped:
            s["state"].append(truncate(stripped, 160))
    # de-duplicate while preserving order
    for k, v in s.items():
        seen, out = set(), []
        for item in v:
            if item not in seen:
                seen.add(item)
                out.append(item)
        s[k] = out
    return s


# ---------------------------------------------------------------- git plumbing


def detect_base(root):
    for ref in ("origin/main", "origin/master", "origin/develop", "main", "master", "develop"):
        if run(["git", "rev-parse", "--verify", "--quiet", ref], cwd=root, check=False).strip():
            head = run(["git", "rev-parse", "HEAD"], cwd=root).strip()
            if run(["git", "rev-parse", ref], cwd=root).strip() == head:
                # we are on the base branch itself; compare with previous commit
                continue
            return ref
    return "HEAD~1"


def get_patch(root, base, working_tree):
    if working_tree:
        return run(["git", "diff", "--no-color", "--no-ext-diff", base], cwd=root)
    merge_base = run(["git", "merge-base", base, "HEAD"], cwd=root, check=False).strip() or base
    return run(["git", "diff", "--no-color", "--no-ext-diff", f"{merge_base}..HEAD"], cwd=root)


def get_commits(root, base):
    merge_base = run(["git", "merge-base", base, "HEAD"], cwd=root, check=False).strip() or base
    out = run(["git", "log", "--no-merges", "--format=%h %s", f"{merge_base}..HEAD"], cwd=root, check=False)
    return [l for l in out.splitlines() if l.strip()][:40]


# ---------------------------------------------------------------- rendering


def build_inventory(files, commits, base):
    inv = {"base": base, "commits": commits, "areas": {}, "files": [], "totals": {"files": 0, "added_lines": 0, "removed_lines": 0, "noise_skipped": 0}}
    for f in files:
        if is_noise(f["path"]):
            inv["totals"]["noise_skipped"] += 1
            continue
        area = classify(f["path"])
        added_sig = extract_signals(f["added"], f["path"]) if not f["binary"] else {}
        removed_sig = extract_signals(f["removed"], f["path"]) if not f["binary"] else {}
        entry = {
            "path": f["path"],
            "old_path": f["old_path"] if f["status"] == "renamed" else None,
            "status": f["status"],
            "area": area,
            "added_lines": len(f["added"]),
            "removed_lines": len(f["removed"]),
            "binary": f["binary"],
            "added": {k: v for k, v in added_sig.items() if v},
            "removed": {k: v for k, v in removed_sig.items() if v},
            "touched_context": touched_context(f["context"]),
        }
        inv["files"].append(entry)
        inv["areas"].setdefault(area, []).append(entry["path"])
        inv["totals"]["files"] += 1
        inv["totals"]["added_lines"] += entry["added_lines"]
        inv["totals"]["removed_lines"] += entry["removed_lines"]
    return inv


def render_markdown(inv):
    out = []
    t = inv["totals"]
    out.append(f"# Change inventory (base: {inv['base']})")
    out.append(f"{t['files']} files changed, +{t['added_lines']} / -{t['removed_lines']} lines"
               + (f", {t['noise_skipped']} generated/lock files skipped" if t["noise_skipped"] else ""))
    if inv["commits"]:
        out.append("\n## Commit messages")
        out.extend(f"- {c}" for c in inv["commits"])

    out.append("\n## Files by area")
    for area in AREA_ORDER:
        paths = inv["areas"].get(area)
        if not paths:
            continue
        out.append(f"\n### {area} ({len(paths)})")
        for e in inv["files"]:
            if e["area"] != area:
                continue
            tag = {"added": "NEW", "deleted": "DELETED", "renamed": "RENAMED", "modified": "modified"}[e["status"]]
            rename = f" (was {e['old_path']})" if e["old_path"] else ""
            out.append(f"- `{e['path']}`{rename} — {tag}, +{e['added_lines']}/-{e['removed_lines']}")

    def section(title, key, label_added, label_removed, limit=25):
        added, removed = [], []
        for e in inv["files"]:
            for item in e["added"].get(key, []):
                added.append((e["path"], item))
            for item in e["removed"].get(key, []):
                removed.append((e["path"], item))
        # something both removed and added in the same file is a modification, not add+remove
        added_set = {(p, i) for p, i in added}
        removed_only = [(p, i) for p, i in removed if (p, i) not in added_set]
        added_only = [(p, i) for p, i in added if (p, i) not in {(p2, i2) for p2, i2 in removed}]
        if not added_only and not removed_only:
            return
        out.append(f"\n## {title}")
        if added_only:
            out.append(f"{label_added}:")
            for p, i in added_only[:limit]:
                out.append(f"- {i}  ← `{p}`")
            if len(added_only) > limit:
                out.append(f"- … {len(added_only) - limit} more (see inventory.json)")
        if removed_only:
            out.append(f"{label_removed}:")
            for p, i in removed_only[:limit]:
                out.append(f"- {i}  ← `{p}`")
            if len(removed_only) > limit:
                out.append(f"- … {len(removed_only) - limit} more (see inventory.json)")

    section("Endpoints and routes", "routes", "Added or changed", "Removed")
    section("Raw SQL", "sql", "Added or changed lines", "Removed lines", limit=15)
    section("Query-builder / ORM calls", "orm", "Added or changed lines", "Removed lines", limit=15)
    section("Schema and migration statements", "schema", "Added", "Removed", limit=20)
    section("Environment / config keys referenced", "env", "Referenced in added code", "No longer referenced")
    section("Feature-flag lines", "flags", "Added", "Removed", limit=10)
    section("Validation / error-raising lines", "validation", "Added", "Removed", limit=15)
    section("Status / state-transition lines", "state", "Added", "Removed", limit=15)
    section("Screen components", "components", "Added or changed", "Removed")
    section("User-visible text in screens", "ui_text", "Added", "Removed", limit=30)
    section("Screen routes / navigation targets", "ui_routes", "Added", "Removed")
    touched = [(e["path"], n) for e in inv["files"] for n in e.get("touched_context", []) if e["status"] == "modified"]
    if touched:
        out.append("\n## Existing functions or blocks whose body was edited (from hunk context)")
        for p, n in touched[:40]:
            out.append(f"- {n}  ← `{p}`")
    section("Functions", "functions", "Added or changed", "Removed", limit=40)
    section("Classes / types", "classes", "Added or changed", "Removed", limit=25)
    section("Tests", "tests", "Added or changed", "Removed", limit=40)

    out.append("\n## How to read further")
    out.append("Pull the diff for one file at a time, only for files this report needs:")
    out.append("`python3 scripts/inventory_diff.py --hunk <path> --max-lines 200`")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="base ref to diff against (default: auto-detect origin/main etc.)")
    ap.add_argument("--working-tree", action="store_true", help="include uncommitted changes")
    ap.add_argument("--repo", help="path inside the repository (default: cwd)")
    ap.add_argument("--out", default=".ticket-review", help="output directory relative to repo root")
    ap.add_argument("--json", action="store_true", help="print inventory.json to stdout instead of markdown")
    ap.add_argument("--hunk", metavar="PATH", help="print the diff hunk for one file from the saved diff.patch")
    ap.add_argument("--max-lines", type=int, default=250, help="truncate --hunk output to this many lines")
    args = ap.parse_args()

    root = repo_root(args.repo)
    if not root:
        sys.exit("not inside a git repository")
    out_dir = ensure_out_dir(root, args.out)

    if args.hunk:
        patch_path = os.path.join(out_dir, "diff.patch")
        if not os.path.exists(patch_path):
            sys.exit("no saved diff.patch — run without --hunk first")
        with open(patch_path, encoding="utf-8", errors="replace") as fh:
            files = parse_diff(fh.read())
        target = args.hunk.strip().lstrip("./")
        for f in files:
            if f["path"] == target or f["path"].endswith("/" + target):
                lines = f["hunk"]
                if len(lines) > args.max_lines:
                    head = lines[: args.max_lines]
                    print("\n".join(head))
                    print(f"\n… truncated: {len(lines) - args.max_lines} more lines. Re-run with a larger --max-lines if this file matters.")
                else:
                    print("\n".join(lines))
                return
        sys.exit(f"file not found in diff: {target}")

    base = args.base or detect_base(root)
    patch = get_patch(root, base, args.working_tree)
    if not patch.strip():
        sys.exit(f"no changes between {base} and {'working tree' if args.working_tree else 'HEAD'}")
    files = parse_diff(patch)
    commits = get_commits(root, base)
    inv = build_inventory(files, commits, base)

    with open(os.path.join(out_dir, "diff.patch"), "w", encoding="utf-8") as fh:
        fh.write(patch)
    with open(os.path.join(out_dir, "inventory.json"), "w", encoding="utf-8") as fh:
        json.dump(inv, fh, indent=1)
    md = render_markdown(inv)
    with open(os.path.join(out_dir, "inventory.md"), "w", encoding="utf-8") as fh:
        fh.write(md)

    if args.json:
        print(json.dumps(inv, indent=1))
    else:
        print(md)


if __name__ == "__main__":
    main()
