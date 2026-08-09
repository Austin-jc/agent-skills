#!/usr/bin/env python3
"""openspec-orchestrate task parser.

Parses an annotated OpenSpec tasks.md (standard checklist + indented
key: value continuation lines) and answers orchestration questions
deterministically so the driving model doesn't re-derive the DAG.

Usage:
  tasks.py validate <tasks.md>     lint annotations, deps, cycles, overlaps
  tasks.py ready    <tasks.md>     unchecked tasks with all deps satisfied
  tasks.py status   <tasks.md>     compact progress summary
  tasks.py show     <tasks.md> ID  full annotation block for one task
  tasks.py waves    <tasks.md>     full topological wave plan (remaining tasks)

Exit codes: 0 ok; 1 usage/IO error; 2 validation errors found.
"""

import re
import sys
from collections import OrderedDict

CHECKBOX = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(?:(T\d+)\s+)?(.*)$")
ANNOT = re.compile(r"^\s{2,}(files|deps|verify|route|note):\s*(.*)$")
KNOWN_ROUTES = {"codex", "direct"}


def parse(path):
    tasks = OrderedDict()
    anon = 0
    cur = None
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    for ln, line in enumerate(lines, 1):
        m = CHECKBOX.match(line)
        if m:
            done, tid, title = m.group(1).lower() == "x", m.group(2), m.group(3).strip()
            if tid is None:
                anon += 1
                tid = f"_anon{anon}"
            cur = {
                "id": tid, "title": title, "done": done, "line": ln,
                "files": [], "deps": [], "verify": None,
                "route": None, "note": None, "anon": tid.startswith("_anon"),
            }
            tasks[tid] = cur
            continue
        m = ANNOT.match(line)
        if m and cur is not None:
            key, val = m.group(1), m.group(2).strip()
            if key in ("files", "deps"):
                cur[key] = [v.strip() for v in val.split(",") if v.strip()]
            else:
                cur[key] = val
            continue
        if line.strip() and not line.startswith((" ", "\t")):
            cur = None  # headers/prose end a task block
    return tasks


def validate(tasks):
    errors, warnings = [], []
    ids = set(tasks)
    seen_titles = {}
    for t in tasks.values():
        loc = f"{t['id']} (line {t['line']})"
        if t["anon"] and any(x["deps"] for x in tasks.values()):
            warnings.append(f"{loc}: task has no T-id; cannot be referenced in deps")
        for d in t["deps"]:
            if d not in ids:
                errors.append(f"{loc}: unknown dep '{d}'")
        if t["route"] and t["route"] not in KNOWN_ROUTES:
            errors.append(f"{loc}: route must be codex|direct, got '{t['route']}'")
        if not t["done"] and not t["verify"] and (t["route"] or "codex") == "codex":
            warnings.append(f"{loc}: codex-routed task has no verify command")
        if not t["done"] and not t["files"] and (t["route"] or "codex") == "codex":
            warnings.append(f"{loc}: no files: boundary declared")
        key = t["title"].lower()
        if key in seen_titles:
            warnings.append(f"{loc}: duplicate title of {seen_titles[key]}")
        seen_titles.setdefault(key, t["id"])
    dup = [i for i in ids if list(tasks).count(i) > 1]
    if dup:
        errors.append(f"duplicate task ids: {dup}")
    # cycle detection (iterative DFS)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {i: WHITE for i in ids}
    for root in ids:
        if color[root] != WHITE:
            continue
        stack = [(root, iter(tasks[root]["deps"]))]
        color[root] = GRAY
        while stack:
            node, it = stack[-1]
            adv = False
            for d in it:
                if d not in ids:
                    continue
                if color[d] == GRAY:
                    errors.append(f"dependency cycle involving {node} -> {d}")
                elif color[d] == WHITE:
                    color[d] = GRAY
                    stack.append((d, iter(tasks[d]["deps"])))
                    adv = True
                    break
            if not adv:
                color[node] = BLACK
                stack.pop()
    # same-wave file overlap
    for wave in compute_waves(tasks):
        owned = {}
        for tid in wave:
            for f in tasks[tid]["files"]:
                if f in owned:
                    errors.append(
                        f"file overlap in same wave: '{f}' claimed by {owned[f]} and {tid}")
                owned[f] = tid
    return errors, warnings


def compute_waves(tasks):
    remaining = {i for i, t in tasks.items() if not t["done"]}
    done = {i for i, t in tasks.items() if t["done"]}
    waves = []
    while remaining:
        wave = sorted(
            i for i in remaining
            if all(d in done or d not in tasks for d in tasks[i]["deps"]))
        if not wave:
            break  # cycle or unsatisfiable; validate reports it
        waves.append(wave)
        done |= set(wave)
        remaining -= set(wave)
    return waves


def fmt_task(t, verbose=False):
    route = t["route"] or "codex*"
    line = f"[{'x' if t['done'] else ' '}] {t['id']}  {t['title']}  (route: {route})"
    if not verbose:
        return line
    out = [line]
    for k in ("files", "deps"):
        if t[k]:
            out.append(f"      {k}: {', '.join(t[k])}")
    for k in ("verify", "note"):
        if t[k]:
            out.append(f"      {k}: {t[k]}")
    return "\n".join(out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, path = sys.argv[1], sys.argv[2]
    tasks = parse(path)
    if not tasks:
        print("no checkbox tasks found")
        sys.exit(1)

    if cmd == "validate":
        errors, warnings = validate(tasks)
        for w in warnings:
            print(f"warn:  {w}")
        for e in errors:
            print(f"ERROR: {e}")
        print(f"{len(tasks)} tasks, {len(errors)} errors, {len(warnings)} warnings")
        sys.exit(2 if errors else 0)

    if cmd == "ready":
        done = {i for i, t in tasks.items() if t["done"]}
        ready = [t for i, t in tasks.items() if not t["done"]
                 and all(d in done or d not in tasks for d in t["deps"])]
        if not ready:
            print("no ready tasks" + (" — all done" if len(done) == len(tasks) else
                                      " — check for cycles/unsatisfied deps (run validate)"))
            return
        for route in ("direct", "codex"):
            group = [t for t in ready if (t["route"] or "codex") == route]
            if group:
                print(f"-- {route} --")
                for t in group:
                    print(fmt_task(t, verbose=True))
        return

    if cmd == "status":
        done = sum(1 for t in tasks.values() if t["done"])
        waves = compute_waves(tasks)
        print(f"{done}/{len(tasks)} done; {len(waves)} wave(s) remaining")
        if waves:
            print("next wave: " + ", ".join(waves[0]))
        return

    if cmd == "waves":
        for n, wave in enumerate(compute_waves(tasks), 1):
            print(f"wave {n}: " + ", ".join(wave))
        return

    if cmd == "show":
        if len(sys.argv) < 4:
            print("usage: tasks.py show <tasks.md> <ID>")
            sys.exit(1)
        tid = sys.argv[3]
        if tid not in tasks:
            print(f"no task {tid}")
            sys.exit(1)
        print(fmt_task(tasks[tid], verbose=True))
        return

    print(f"unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    main()
