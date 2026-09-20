"""Shared helpers for the ticket-review scripts. Standard library only."""
import os
import re
import subprocess

AREA_RULES = [
    ("tests", re.compile(r"(^|/)(tests?|__tests__|spec|specs)(/|$)|[._-](test|spec)\.[a-z]+$|_test\.go$", re.I)),
    ("migrations", re.compile(r"(^|/)(migrations?|migrate|alembic|db/migrate)(/|$)|schema\.prisma$|\.sql$", re.I)),
    ("database", re.compile(r"(^|/)(repositor(y|ies)|repos?|models?|entities|entity|dao|queries|query|db|schema|orm)(/|$)|(repository|model|entity|query|queries)\.[a-z]+$", re.I)),
    ("api", re.compile(r"(^|/)(routes?|routers?|controllers?|handlers?|api|endpoints?|graphql|resolvers?)(/|$)|(route|router|controller|handler|resolver)s?\.[a-z]+$", re.I)),
    ("screens", re.compile(r"\.(tsx|jsx|vue|svelte|css|scss|less|html)$|(^|/)(components?|pages?|views?|screens?|ui|layouts?|widgets?)(/|$)", re.I)),
    ("config", re.compile(r"(^|/)\.env|\.(ya?ml|toml|ini|cfg|conf)$|(^|/)(config|settings|configs)(/|$)|Dockerfile|docker-compose|package\.json$|Cargo\.toml$|pyproject\.toml$|tsconfig|\.github/", re.I)),
    ("services", re.compile(r"(^|/)(services?|domain|usecases?|use_cases?|logic|core|business|workflows?|jobs?|tasks?|commands?)(/|$)|(service|usecase|job|worker)s?\.[a-z]+$", re.I)),
    ("docs", re.compile(r"\.(md|rst|txt)$|(^|/)docs?(/|$)", re.I)),
]

AREA_ORDER = ["screens", "api", "services", "database", "migrations", "config", "tests", "docs", "other"]

NOISE_PATHS = re.compile(
    r"(^|/)(node_modules|dist|build|target|vendor|\.git|__pycache__|\.next|coverage)(/|$)"
    r"|(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|poetry\.lock|\.min\.(js|css))$",
    re.I,
)


def classify(path):
    for area, rx in AREA_RULES:
        if rx.search(path):
            return area
    return "other"


def is_noise(path):
    return bool(NOISE_PATHS.search(path))


def run(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{result.stderr.strip()}")
    return result.stdout


def repo_root(start=None):
    try:
        return run(["git", "rev-parse", "--show-toplevel"], cwd=start or os.getcwd()).strip()
    except RuntimeError:
        return None


def ensure_out_dir(root, out):
    path = out if os.path.isabs(out) else os.path.join(root, out)
    os.makedirs(path, exist_ok=True)
    return path


def truncate(text, limit):
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
