# Review — make the new org operational (#868)

branch: feat/868-org-operational
diff_sha256: 20426e42c2e02f362115b48fea444d8ba62adbd5ddce727cb991eed6a7294a40
rounds: 6
rounds_cap_override: CPO 2026-07-31. Asked in plain words "May I go past three to write those tests?" he answered "yes". Rounds 4, 5 and 6 are that grant being spent on what it was given for: round 4 found that one of the very tests round 3 demanded would have reddened CI on every pull request, and rounds 5 and 6 corrected two factual errors the fixes introduced. Both round-3 ESCALATE questions were put to him in plain words and answered; both answers are recorded in `.claude/task/escalations.log` under 2026-07-31, not only here.

> **All three required reviewers PASS at this hash.**
>
> What six rounds caught, because it is the case for the process and not one style note among it.
> **Round 1** — two §10 violations of mine: `report_process_health.py` claimed a CPO ruling that does
> not exist, and the handover turned my own invented threshold into a rule for withdrawing his
> process. Plus a vacuous test that would have passed with the gate disabled, and a credentials guard
> the split had silently narrowed.
> **Round 2** — my round-1 fix bought unapproved opus review time. The cheap remedy was to correct the
> prose; I had widened the routing rows instead. Reverted.
> **Round 3** — two new gate branches with no test, the same class already flagged twice; plus two §10
> questions escalated rather than decided.
> **Round 4** — the test written to answer round 3 **would have reddened CI on every pull request**,
> because it read real git history while `python-ci.yml` checks out at `fetch-depth: 1`. The script
> under test documents that exact shape and handles it; my test asserted it could not happen. Also:
> both CPO rulings were recorded only in `contract.md`, which the next task overwrites.
> **Round 5** — two factual errors of mine. A row count copied from a reviewer without counting it
> (10 where it is 11), propagated into two documents including the durable log. And a caveat claiming
> "nothing catches a secret in CI", written into three places and used to put a cost question to the
> CPO, which was **false**: `security-secrets.yml` runs gitleaks on every PR with a fail-closed gate.
> **Round 6** — both corrections verified by me against the primary sources, then by both reviewers
> independently recounting and re-reading the workflow rather than accepting my summary.
>
> Machine gates green throughout: **240 tests**. Four issues filed (#870-#873). Residue is listed
> under each reviewer as `owed`, never hidden.

## scope-auditor

Escalated two §10 questions in round 3; both were put to the CPO in plain words and answered.

CPO ANSWER (2026-07-31) on the credentials guard's review tier: **"yes"** — put it back on
`cto-reviewer` as well. It now sits on three reviewers, so coverage is strictly wider than before the
split at no extra cost, because the CTO is already spawned at opus on those paths.

CPO ANSWER (2026-07-31) on `docs/north_star.md`'s roles roster: **"yes, update"**. The roster now
carries a **Wakes on** column checked row-for-row against `review_routing.json`, and
`docs/north_star.md` is in `scope_paths` via a recorded amendment.

VERDICT: PASS
risks_checked:
- The count that failed twice. Rather than accept round 5's "11", counted the rows containing
  `cto-reviewer` directly in `.claude/review_routing.json:136-146` and got 11, then checked
  `docs/north_star.md`'s decomposition (8 guard paths + `*requirements*.txt` + `site_v2/package.json`
  + `package-lock.json`) against the JSON's own "eight guard paths" statement. Consistent. Then swept
  the repo for any third document carrying a stale count: none exists, so the propagation path that
  produced the defect is closed rather than patched at two sites.
- Guard-loosening under cover of a factual correction. The retracted CI-coverage caveat could have
  been used to soften the credentials hunt item. Read `security-secrets.yml` in full: gitleaks on
  every `pull_request` and push to `main`, terminal `gate` with `needs` + `if: always()` exiting 1 on
  any non-success, so it fails CLOSED and the correction is true. `cto-reviewer.md` still ends item 6
  in "→ FAIL" and still asserts triple coverage, so no coverage was removed; the reserved item is
  struck through with its residual question retained, so a false premise was retracted without a §10
  decision being taken in its place.
- Scope on the delta: 18 files, every one inside `scope_paths` (`docs/north_star.md` via the recorded
  amendment), no new file since round 5.

## cto-reviewer

VERDICT: PASS
risks_checked:
- Hunt item 6's secret-scanning description re-verified against the workflow itself, not the builder's
  summary. `security-secrets.yml` triggers on unfiltered `pull_request` and on push to `main`, runs
  `gitleaks-action@v2`, and its terminal `gate` job exits 1 on any non-success, so "CI scanning exists
  and fails CLOSED" is true and the earlier "nothing catches a secret in CI" claim is gone from all
  three places. A grep of the entire `.github` tree confirms no workflow invokes
  `.pre-commit-config.yaml`, `check_no_secrets.py` or `detect-private-key`, so the "LOCAL-ONLY second
  layer" half is accurate too.
- The delta does not weaken the guard it edits. Item 6 keeps its categorical FAIL trigger and adds
  only machine-layer facts plus a "check the workflow, do not infer the coverage" instruction. The
  withdrawn reservation is struck through and marked, not deleted, so `contract.md` stays consistent
  with `escalations.log`, and the residual question stays RESERVED rather than absorbed — correct,
  because wiring the local hooks would be a new mechanism plus recurring build minutes. Row count
  independently recounted from the JSON: 11. `protected_override` and a non-placeholder `impact_map`
  are present and unchanged.
- Adding a hunt item to my own brief, on a commit where I am the only required specialist, judged for
  honesty: items 1-5 unchanged, old items 6 and 7 survive verbatim as 7 and 8, nothing narrowed or
  dropped. A builder weakening its adversary removes items; this one added one and volunteered a
  caveat against its own interest. The reallocation is not a recurring cost — the CTO is already
  spawned on all eight guard paths, unlike round 2's row widening, which correctly failed on exactly
  that.

owed, not blocking:
- The deferred amendment landed. `decisions_taken` now carries the credentials reallocation and the
  declaration that `report_process_health.py` ships builder-initiated and unruled; `decisions_reserved`
  carries the copy-gate wiring, so `check_copy_gate.py`'s docstring claim is finally true.
- Whether branch protection actually requires the `gate` check is not verifiable in-repo.

## platform-reviewer

VERDICT: PASS
risks_checked:
- The round-4 blocker is genuinely closed and not merely relocated. `python-ci.yml` still checks out
  at the default `fetch-depth: 1` and still runs `pytest tests/`, and the health test no longer
  asserts anything about real history: `_fake_git` intercepts the script's single git wrapper, so
  `total == 2` comes from the fixture. Swept the rest of `tests/` for the same hazard — every
  remaining real-git call is a temp-repo fixture or `git ls-files`, both depth-1-safe.
- Both new tests fail on revert, traced assertion by assertion. Reverting the counter seeding breaks
  `briefs <= set(hits)`; reverting the `if not total:` early return raises `ZeroDivisionError` because
  the seeded counter makes the loop run, and the `capsys` assertion still fails even if seeding is
  reverted at the same time. `_fake_git`'s dispatch matches how `activation()` and `rounds_history()`
  actually call `_git`, including the `args[-1]`-is-the-sha assumption and the empty-history edge.
  `monkeypatch` restores the module attribute and `_health()` balances its `sys.path` mutation.
- The acceptance gate preserves fail-open: `_acceptance_gate` runs inside `_commit_gate`, wrapped
  `try/except Exception`, so an OSError on the contract or evidence file cannot lock commits; and it
  delegates rather than double-denying when no contract exists, with a test that calls it directly.
  `check_copy_gate.main()` fails CLOSED on every failure path. Neither inverted.

owed, not blocking:
- `assert hits["seo-expert-reviewer"] == 0` is vacuous alone (`Counter.__missing__` returns 0); the
  revert is caught by the `briefs <= set(hits)` line above it. Reword on the next touch.
- `report_process_health.py` derives `routing`/`briefs` twice and hardcodes `name != "scope-auditor"`.
  Worst case is a wrong annotation on a printed line in a script that decides nothing.
- The reporting block at `:170-180` never executes under test, since the tests reach `main()` only on
  the empty-history path. Acceptable for a CI-unwired reporter; not if #872 wires it.
- The acceptance gate has no CI twin (#870), and `acceptance_evidence.md` is read from the working
  tree and never required to be staged, so it can be satisfied by a file that never enters the commit.

## Machine gates — green every round

- `python -m pytest tests/test_governance_hooks.py` — **240 passed**.
- `python scripts/check_layer_contract.py` — passed.
- `review_routing.json` parses with `object_pairs_hook` rejecting duplicates: 29 unique keys.
- Activation measured at this hash: `cto-reviewer` 28% to 12%, `platform-reviewer` 24%, 10% both;
  0 of 48 tracked `site_v2/src/**` files require either.
- All 8 agent briefs carry a byte-identical `## Delta re-review`.
- `python scripts/check_copy_gate.py` exits 1 with 16 findings, as designed and disclosed (#872).
- `python scripts/report_process_health.py` surfaces `seo-expert-reviewer` at 0% DEAD, NO ROUTING ROW.
