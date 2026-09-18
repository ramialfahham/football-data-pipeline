# Review — docs/github-mirror — 2026-09-18

diff_sha256: 6ff23fff43c2cc643d02b981841eebe1df15402dcccf81d770c78090d8aae1cc

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed file (`CLAUDE.md`, `README.md`, `.github/workflows/README.md`, `.github/ISSUE_TEMPLATE/config.yml`, the two skills, `scripts/check_task_artifacts.py`, `tests/test_governance_hooks.py`, the contract) is in `scope_paths`; nothing touched outside the declared surface.
- Protected path `.github/workflows/README.md`: `protected_override` quotes the CPO's 2026-09-18 chat ruling naming this file with a date; the diff to it is prose only; the eleven `.yml` files and `_paused/` show zero hunks, matching `done_when`.
- §10 content decision (README badge removal): `decisions_taken` gives the reason (the GitLab badge 404s to a visitor, `public_jobs: false`) and `refs` quotes the CPO's "go, yes fix the readme badges too" with the date — not a silent decision.
- New mechanisms / recurring cost: none in the diff; the mirror was configured in GitLab settings before the branch and no workflow is re-enabled or edited.
- Secrets: every hunk swept; only the sentence that the token lives in GitLab's mirror settings and is the CPO's, no value.
- `decisions_reserved`: `docs/operations_guide.md` and `docs/development_workflow.md:62` named as out-of-scope stale text and confirmed absent from the diff.
- Round 2: only `contract.md` changed; the kept historical sentence at `.github/workflows/README.md:13` is a pre-existing context line, untouched by the diff, and the amended `done_when` ("exactly one hit") is honest against the patch.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `protected_override` quotes a specific CPO chat ruling from 2026-09-18 naming `.github/workflows/README.md` explicitly; confirmed against `review_routing.json` (routes `.github/workflows/**` to cto + platform) and `task_contract_gate.py:64` (`PROTECTED_PREFIXES`) that the override is invoked on the path the guard actually protects.
- Workflow `.yml` files: the patch's `diff --git` blocks under `.github/` are the README and `ISSUE_TEMPLATE/config.yml` only; zero `.yml` under `.github/workflows/`.
- Guard invariant: `default_base()` in `scripts/check_task_artifacts.py:87-115` — only the docstring changed; the executable body is byte-identical. The renamed test keeps its `== "gitlab/main"` / `== "origin/main"` assertions; no test weakened.
- `impact_map` "writers: none": independently grepped `workflows/README` across the tree — only `CLAUDE.md`, the contract, the artifact-only tracker snapshot and the patch itself; no script, hook or workflow parses it.
- New mechanism / dependency / recurring cost: none; badge removal is a deletion with its reasoning in `decisions_taken`.
- Credentials: full diff scanned; no key, token or permission-widening line.
- Round 2: only `contract.md` changed; keeping a true past-tense sentence versus a present-state claim is an editorial distinction inside the prose-only work the override already authorises — no separate sign-off, no guard, no cost.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `default_base()` (`scripts/check_task_artifacts.py:87-115`): only the docstring changed; `env = os.environ.get(...)`, the `subprocess.run(["git","remote"])` call and the `"gitlab/main" if "gitlab" in remotes else "origin/main"` return are byte-identical. No behaviour change.
- `tests/test_governance_hooks.py`: the renamed test `test_default_base_prefers_the_live_remote_over_the_mirror_origin` keeps its assertions; `grep -rn dormant_origin` across the tree finds no reference to the old name outside the patch file — no orphaned `-k` selector or cross-reference.
- `.github/workflows/README.md` claims checked against the actual `.yml` files: the seven `on: push: branches: [main]` workflows verified by grep (the other four do not trigger on push); the two crons `0 4 * * *` and `30 7 * * *` match 04:00/07:30 UTC; the three prod writers (`dbt-scheduled.yml:43`, `pages-match-preview.yml:81` `target: prod`; `ci-data-build.yml` `--target prod` at 138/208/214/227 with `target: ci` default at 93) match; the `#667` concurrency-group quote is verbatim from `ci-data-build.yml:57-59`.
- No `.yml` under `.github/workflows/` in the patch; the GitHub repo URL is consistent everywhere it is cited; no other file contradicts the mirror / Actions-disabled claim.
- Round 1 FAIL: the contract's `done_when` grep, run as written, returned one hit (`.github/workflows/README.md:13`, the historical "after the GitHub account was suspended") that the criterion said would be zero, undisclosed. Round 2: `decisions_taken` names it as deliberately kept (a past fact about why the migration happened, not a current-state claim) and `done_when` expects exactly that one hit; re-ran the grep — exactly one hit, that line. Only `contract.md` changed between rounds; the other eight file diffs are byte-identical to round 1.

## escalations
(none)
