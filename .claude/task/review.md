# Review — fix/22-23-24-migration-residue — 2026-08-07

diff_sha256: 805a595f970949af20b75a97d2f1b15fc709fece2fd37ac4e9e9684d3abce029

rounds: 2

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 was a FAIL: `protected_override` and `amendments` claimed CPO authority with NO entry in
  `escalations.log`. Round 2 confirms the citations now resolve exactly — the log gains a pure
  append at the tail (`@@ -1288,3 +1288,55 @@`, no prior line modified, so it stays append-only per
  §2) headed `2026-08-07 fix/22-23-24-migration-residue`, and the contract cites its two block
  titles verbatim.
- The two cited anchors say what the entry claims: `escalations.log:1186` is the CPO answering (b)
  "record it, file it, and fix it in its own task" for the territory omission, filed as #22 — this
  task; `:1203` files #23 likewise. Citing rather than restating them is correct, and the override
  is anchored by two rulings that predate this branch.
- The class fix rather than a fourth instance fix: the entry logs the failure before the ruling,
  names all four instances by line (`:1156`, `:1238`, `:1287`, this one), cites the governing
  ruling at `:112`, and states the habit change — the log entry and the `protected_override` are
  ONE action. The three prior fixes each corrected an instance, which is why four were countable.
- Override reach versus the diff: `.claude/agents/platform-reviewer.md` changes only the territory
  sentence; `.gitlab-ci.yml` only `#` lines. `.github/workflows/**`, `.claude/review_routing.json`,
  the protected list in `task_contract_gate.py` and `.claude/hooks/stop_gate.py` are all absent
  from the patch. The diff stays inside the stated reach.
- The guard was SATISFIED, not loosened. The corrected sentence's path run equals
  `shared_guard_paths()`, which `_allowed_runs` already admits, so `KNOWN_INCOMPLETE` empties
  because the prose became correct. Emptying it REMOVES an exemption, which is a strengthening.
- `check_task_artifacts.py`: `.gitlab-ci.yml:279` passes `--base` explicitly, so `default_base()`
  is never reached in CI and CI behaviour is unchanged. `GOVERNANCE_BASE` is consulted first and is
  pinned by a test. No check removed; the error direction moves from a stale base to the live one.
  The NARROWING classification is agreed.
- GitHub dormancy: nothing forecloses a return. The fallback stays `origin/main` and is pinned by a
  test, the territory sentence keeps `.github/workflows/`, and `CLAUDE.md` says dormant, not
  retired.
- Delta basis, stated rather than assumed: every non-artifact hunk carries the same pre- and
  post-image blob hashes as round 1, so only `contract.md` and `escalations.log` moved and round 1's
  full audit still holds. Procedural note from the reviewer, recorded because it is correct: its
  round 1 was a FAIL, so this is strictly a re-review rather than the post-PASS delta its brief
  defines, and it accepted the narrowed scope only because the unchanged blob hashes prove it.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `default_base()` reach, verified from code not the contract: `--base` defaults to `None` and the
  resolver is called only then, so the subprocess never runs when a base is passed. Both real
  callers pass one. CI behaviour is byte-identical; only a bare local run changes.
- Failure and re-run modes: read-only and idempotent. No `check=True`, so a non-zero `git remote`
  yields empty stdout and the `origin/main` fallback; `timeout=10` raises `TimeoutExpired`, caught
  by `except Exception`; membership is exact, so a remote named `gitlab-mirror` does not match.
  Noted improvement the builder had not claimed: `GOVERNANCE_BASE=""` now falls through to
  detection instead of producing the empty base the old default produced.
- Fail-closed direction: no new exit-0 path. Every error branch still returns 1.
- Test discrimination, answered precisely: `test_default_base_falls_back_when_git_cannot_be_queried`
  does NOT discriminate against the old hardcoded default, because it asserts `origin/main`, which
  is what the old code returned. That is CORRECT rather than a defect — it pins the `try/except`
  and reds if the handler is removed. The preference is pinned by the second assert of
  `test_default_base_prefers_the_live_remote_over_a_dormant_origin`, which reds against the old
  default. Residual recorded, not failed: nothing pins `main()`'s two-line wiring, so a partial
  revert keeping the function but restoring the argparse default would stay green.
- `.gitlab-ci.yml` comment-only claim, checked against the patch: one hunk, three `#` lines out and
  four in. The job's `variables`/`cache`/`script`/`rules`, the `*not_on_schedule` and
  `*site_v2_paths` anchors and the `.gcp_job` `id_tokens` block are untouched. The new comment's own
  claim also holds: `deploy:site-v2`'s only rule is `$CI_PIPELINE_SOURCE == "web"`, so manual-only
  is accurate.
- Empty `KNOWN_INCOMPLETE`: no repo pytest config, so `empty_parameter_set_mark` defaults to skip —
  one collected, skipped item, suite green. Empty makes `test_every_protected_path_list_is_complete`
  strictly stronger, and adding an entry re-arms the pairing test automatically. Correct steady
  state, not a silent hole.
- Duplicated enforcement: the hand-copied reviewer loop, the round-cap import and the hash-exclude
  pathspec are unchanged in both twins, so nothing was fixed in one copy only.
  `git_discipline._base_commit` is a separate resolution and is untouched.
- The skill edits are as re-runnable as the form they replace, and a machine without a `gitlab`
  remote now fails loudly at fetch rather than silently branching from a stale ref. The edited
  sentence sits OUTSIDE the `FAST_GATES` markers, so `test_fast_gates_and_validate_local_agree` is
  unaffected.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 was a FAIL on the scope-widening amendment citing a CPO quote with no `escalations.log`
  entry — the identical defect this reviewer failed the sibling branch for twice in the same
  session. Round 2 confirms the entry exists, that every quote and cited line number resolves to a
  real prior ruling rather than an invented one, and that both contract blocks now cite it.
- Threshold-declaration accuracy: counted the actual new test functions in the diff (three) against
  the corrected `decisions_taken` ("THREE added unit tests") and the corrected `done_when` (648
  collected, not 646). Both now match the diff rather than an unverified prediction.
- Scope containment: every changed file is in `scope_paths`; `.github/workflows/`, the routing
  table, the protected list and `stop_gate.py:53` are untouched, matching the override's explicit
  disclaimers.
- Credentials and permissions: swept the full diff. Nothing credential-shaped, no permission
  widening, `id_tokens` and `rules:` untouched.

## escalations
- question: The sweep found SIX sites carrying the stale governance base where GitLab #24 listed
  three, the worst being `onboard-competition/SKILL.md`, which branched new work from a tree 27
  commits behind. Fix only the three the issue named, or all six?
  CPO ANSWER: "fix all six, and file the skills gap" (conversation, 2026-08-07). Recorded in
  `escalations.log` under `⭐ CPO RULING: SCOPE WIDENED from three sites to six`; the skills gap is
  filed as GitLab #27.

## Note on the round-1 failure, recorded rather than left in the diff
Two of three reviewers FAILed round 1 on the same finding: the contract claimed CPO authority that
no durable record carried. `cto-reviewer` counted it as the FOURTH occurrence in one session
(`escalations.log:1156`, `:1238`, `:1287`, and this task). Each earlier one was fixed by adding the
one missing entry, and none changed the habit that produced it. The class fix is recorded in the log
entry: the `escalations.log` entry and the `protected_override` are written in the SAME action.
