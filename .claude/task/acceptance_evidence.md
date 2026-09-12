# Acceptance evidence — the tracker has a backup in the repo

criteria_demonstrated:
  - THE SCRIPT WRITES THE SNAPSHOT FROM THE LIVE TRACKER. `python scripts/snapshot_tracker.py` →
    "wrote docs\tracker\gitlab_snapshot.md: 7 milestones, 142 issues, 490,795 chars" through the
    existing `glab` login (no token added; `glab api` paginated at 100 per page, all states,
    `scope=all`). The header: the banner sentence (a BACKUP … read only when GitLab is unreachable,
    never edited by hand … the GitLab issue is the source), the UTC stamp, `sha256(body)`. The
    body: the milestone list, then every issue under its milestone (`### #iid title`, state,
    dates, labels, the body verbatim), then "No milestone" — 142 `### #` headings counted, order
    deterministic (`test_render_is_deterministic_and_groups_by_milestone` renders reversed input
    to the identical text). The checksum recomputed over the committed file → equal. The first
    snapshot is staged on this branch. Checked against the two tree guards before tracking it:
    `host_fingerprint_gate.flagged_lines` over the whole file → 0; the comment gate does not
    govern `.md`.
  - NOBODY CAN EDIT IT. Live in this session, a real `Edit` of the snapshot's first heading was
    refused with the hook's own text ("`docs/tracker/` is the generated backup … has one writer
    … run `python scripts/snapshot_tracker.py`"). `tests/test_tracker_snapshot.py` (22 tests):
    the committed header's sha256 equals the body's; a one-character change differs; on a temp
    repo a `Write`, an `Edit` and a `MultiEdit` to the snapshot are denied, a new file under the
    folder is denied, three differently-cased spellings of the folder (`Docs/Tracker`,
    `DOCS/TRACKER`, `docs/Tracker` — the same folder on Windows) are denied, five other paths
    pass (including `docs/trackers/x.md` and `docs/tracker.md`, the near-misses), a path outside
    the repo passes, six malformed inputs fail open, `is_governed` pinned directly, the wiring
    pinned, the three routing entries pinned and `artifact_only_never` clear — 25 tests. MUTATION
    shown red (case): the case fold removed from `is_governed` → the three spellings' tests
    FAIL (3 failed); restored, 25 passed. MUTATION shown red (checksum): one phrase changed in the
    committed snapshot's body by a Python write (the door the hook cannot see) →
    `test_the_committed_snapshot_is_exactly_what_the_script_wrote` FAILS with "the body was
    changed without rewriting the header"; restored, 22 passed. WHAT THIS DOES NOT PROVE (the
    cto-reviewer's round-1 finding): the checksum is computed by the same process that writes the
    body, so a deliberate shell write that also recomputes the header passes — self-consistency,
    not provenance. The guarantee as first stated ("any change the script did not make") was
    overstated; corrected in the contract, this file, the `CLAUDE.md` row, the guardrails row and
    both docstrings, and said to the product owner.
  - IT CANNOT BE CITED. `CLAUDE.md` "Which source answers which question" gains a fifth row,
    labelled "(backup only)", saying what the file is, who writes it, that a hook refuses a hand
    edit and a test checks its checksum, and that it is never cited while GitLab is up; the four
    original rows are untouched. The operational notes gain the session-end line.
  - IT CANNOT DRIFT FAR. `docs/tracker/**` is in `hash_exclude_paths`, `review_exclude_paths`
    and `artifact_only`: `--staged-hash` with the snapshot staged, then the script re-run (new
    timestamp) and re-staged → the same hash (`9c57597b…` both times); the regenerated review
    patch carries no `diff --git` for the file and lists it under "NOT SHOWN — BUT THESE FILES
    ARE EDITED". The handover names the routine: run the script at the end of every session,
    before the handover commit.
  - SUITES. `pytest tests/test_tracker_snapshot.py` → 25 passed; the two tree guards
    (`test_no_dead_issue_refs.py`, `test_no_host_fingerprint_in_tree.py`) → 52 passed with the
    snapshot present. The first full run (22-test version) found a third tree walker the
    snapshot collides with: `test_materialisation_policy.py` read an old issue body quoted in the
    snapshot ("Staging as view") as a live claim of the repo — 2 failed. The snapshot is a
    quotation of the tracker, the class that test's `_is_bookkeeping` already exempts for
    `docs/product_direction_threads.md`; `docs/tracker/` joins it (one line, reasoned in place),
    and that file plus the snapshot test → 33 passed. The second full run found a fourth walker,
    `test_governance_doc_parity.py` (it uses `git grep`, so an `ls-files` search for walkers
    missed it): every file mentioning a guard or protected path must be checked or exempted with
    a reason; the snapshot joins `SWEEP_EXEMPT` beside `docs/audits/` with its reason — 1 failed
    → the three affected files 72 passed, 1 skipped. THE PATTERN, for the next walker's author:
    the snapshot is a file that RECORDS, not one that GOVERNS. A walker that hunts stale CLAIMS
    (materialisation policy, guard-path facts) exempts `docs/tracker/` with that reason, beside
    its existing history exemptions; a walker that hunts a PROPERTY true of any file regardless
    of intent (a public address) keeps scanning it. Three of the former, one of the latter, today.
    `pytest tests/` on the final code → **1,157 passed, 1 skipped, 14 subtests passed** (9:23) —
    `main`'s 1,132 plus the 25 new; `ruff check --config .ruff-ci.toml`
    on the script, the hook and the three tests → "All checks passed!".

## What is NOT demonstrated
- The session-end refresh is a routine, not a mechanism: nothing fires if a session ends without
  running the script. The file then goes stale by one session at a time and says so in its own
  timestamp. A scheduled refresh is reserved.
- Merge-request heads (where code decisions are recorded) are not in the snapshot — reserved.
- A shell write into `docs/tracker/` bypasses the hook like every edit-time gate; the checksum
  test catches it only if the writer did not also recompute the header (the mutation above is
  that case). A writer who forges the header is not caught by anything in the repo; CI
  re-reading GitLab would catch it and needs a token — reserved, the product owner's. The
  exposure is the same class the handover already carries, with no hook on it at all.
- The snapshot is 490 KB and grows with the tracker; it is hash- and review-excluded, so it
  costs no review tokens, but every session-end commit rewrites the whole file.
