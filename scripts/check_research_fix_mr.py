#!/usr/bin/env python
"""Is this merge request a research-fix MR?

    python scripts/check_research_fix_mr.py --base <ref> [--head <ref>]

Exit 0: a research-fix MR. Exit 1: not one, with every reason. Exit 2: cannot decide.

A research-fix MR changes only rows of the correction seeds the research skill writes to, and
its own task folder. Each added or changed row names its source, and every source is on a site
the skill reads. The merge hook lets such an MR through once its pipeline is green.

The allowed sites are the skill's own tables, read from the skill on the merge base: a site the
skill does not list, a stopped site included, is refused.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
import sys
from urllib.parse import urlparse

SKILL = ".claude/skills/research-provider-errors/SKILL.md"
SEED_DIR = "dbt_project/seeds/"
SEED_KEYS = {
    "fixture_card_corrections": ("fixture_id", "card_order"),
    "fixture_goal_corrections": ("fixture_id", "goal_order"),
    "fixture_result_corrections": ("fixture_id",),
}
SEEDS = {f"{SEED_DIR}{name}.csv": key for name, key in SEED_KEYS.items()}
TASK_FILE = re.compile(r"^\.claude/task/([^/]+)/[^/]+$")
HOST = re.compile(r"`([a-z0-9][a-z0-9.-]*\.[a-z]{2,})`")
TABLE_START = "## Site table"
TABLE_END = "Not read, and the reason:"


class Undecided(Exception):
    pass


def git(args: list[str], cwd: str | None = None) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        raise Undecided(f"`git {' '.join(args[:2])}` failed: {r.stderr.strip()[:200]}")
    return r.stdout


def show(ref: str, path: str, cwd: str | None = None) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def allowed_hosts(skill_text: str) -> set[str]:
    """The hosts the skill reads: its site table and its news-outlet list, down to the stopped sites."""
    start = skill_text.find(TABLE_START)
    end = skill_text.find(TABLE_END, start)
    if start < 0 or end < 0:
        raise Undecided("the skill's site table could not be found")
    hosts = set(HOST.findall(skill_text[start:end]))
    if not hosts:
        raise Undecided("the skill's site table holds no host")
    return hosts


def parse_seed(text: str, name: str) -> tuple[str, dict[tuple, dict], list[str]]:
    """(header line, rows by key, problems)."""
    header = text.splitlines()[0] if text.strip() else ""
    key_cols = SEEDS[f"{SEED_DIR}{name}.csv"]
    reader = csv.reader(io.StringIO(text))
    names = next(reader, [])
    rows: dict[tuple, dict] = {}
    problems: list[str] = []
    for n, values in enumerate(reader, start=2):
        if not values:
            continue
        if len(values) != len(names):
            problems.append(f"{name} line {n}: {len(values)} fields, the header has {len(names)}")
            continue
        row = dict(zip(names, values))
        if any(c not in row for c in key_cols):
            problems.append(f"{name}: no key column {key_cols}")
            break
        key = tuple(row[c] for c in key_cols)
        if key in rows:
            problems.append(f"{name} line {n}: key {key} appears twice")
        rows[key] = row
    return header, rows, problems


def source_problems(source: str, hosts: set[str]) -> list[str]:
    urls = source.split()
    if not urls:
        return ["no source"]
    out = []
    for u in urls:
        p = urlparse(u)
        if p.scheme != "https" or not p.hostname:
            out.append(f"source {u} is not an https URL")
        elif p.hostname.lower() not in hosts:
            out.append(f"source host {p.hostname.lower()} is not on the skill's list of sites it reads")
    return out


def seed_problems(name: str, old: str | None, new: str | None, hosts: set[str]) -> list[str]:
    if new is None:
        return [f"{name} is deleted"]
    if old is None:
        return [f"{name} is new; a research-fix MR only adds rows to a seed that exists"]
    old_header, old_rows, _ = parse_seed(old, name)
    new_header, new_rows, problems = parse_seed(new, name)
    if old_header != new_header:
        problems.append(f"{name}: the header changed")
    for key in old_rows:
        if key not in new_rows:
            problems.append(f"{name}: the row {key} is removed; a research-fix MR only adds or changes rows")
    for key, row in new_rows.items():
        if old_rows.get(key) == row:
            continue
        for p in source_problems(row.get("source", ""), hosts):
            problems.append(f"{name} row {key}: {p}")
    return problems


def decide(base: str, head: str, cwd: str | None = None) -> list[str]:
    """Why this is not a research-fix MR; an empty list means it is one."""
    merge_base = git(["merge-base", base, head], cwd).strip()
    changes = [ln.split("\t", 1) for ln in git(["diff", "--name-status", "--no-renames", merge_base, head],
                                                cwd).splitlines() if ln.strip()]
    if not changes:
        return ["the MR changes nothing"]
    problems: list[str] = []
    folders: set[str] = set()
    seeds: list[str] = []
    for _status, path in changes:
        m = TASK_FILE.match(path)
        if m:
            folders.add(m.group(1))
        elif path in SEEDS:
            seeds.append(path)
        else:
            problems.append(f"{path} is not a correction seed the research skill writes to")
    if len(folders) > 1:
        problems.append(f"more than one task folder is changed: {', '.join(sorted(folders))}")
    if not seeds:
        problems.append("no correction seed is changed")
    if problems:
        return problems
    skill = show(merge_base, SKILL, cwd)
    if skill is None:
        raise Undecided(f"{SKILL} does not exist on the merge base")
    hosts = allowed_hosts(skill)
    for path in seeds:
        name = path[len(SEED_DIR):-len(".csv")]
        problems += seed_problems(name, show(merge_base, path, cwd), show(head, path, cwd), hosts)
    return problems


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True, help="the target branch, e.g. origin/main")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args(argv)
    try:
        problems = decide(args.base, args.head)
    except Undecided as e:
        print(f"cannot decide: {e}", file=sys.stderr)
        return 2
    if problems:
        print("NOT a research-fix MR:")
        for p in problems:
            print(f"- {p}")
        return 1
    print("research-fix MR: only correction-seed rows, each with its source on a site the skill reads")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
