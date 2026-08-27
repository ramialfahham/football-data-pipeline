# Review — fix/92-singular-tests-read-the-branch — 2026-08-27

> #92, in two halves: `--favor-state` removed from `data:build:mr`'s `dbt test` line so the 30
> singular tests read the BRANCH, and the CI target made per-merge-request
> (`DBT_CI_TARGET=ci_mr${CI_MERGE_REQUEST_IID}`) so no branch can read another's tables.
> Branched from main `1804a64`.
> PROTECTED path (`.gitlab-ci.yml`) → `cto-reviewer` + `platform-reviewer` at the **opus** floor,
> plus the always-on `scope-auditor`; `dbt_project/**` adds `analytics-engineer-reviewer`.

diff_sha256: 74d096637de615529f58ab9be17ec430d0a88de383d30f0b4637bc4a31c268f3

rounds: 9

rounds_cap_override: >
  The cap is 3. This ran to NINE, and the honest reason is that the work changed shape after review
  had already passed it — not that a disagreement was re-litigated.
  Rounds 1-3 reviewed HALF ONE (the flag) and ended in four PASSes; it was committed. CI then proved
  half one insufficient on the very first pipeline, which is evidence no review could have produced.
  The CPO was shown that failure and answered **"fix it"**; shown the storage question, he answered
  **"go ahead"** and set the standing constraint that nothing here go near a warehouse-deleting
  mechanism. Those are the say-so this override rests on, all quoted verbatim in `escalations.log`.
  ⛔ AND THE ROUND COUNT IS ITSELF A FINDING, recorded rather than smoothed over. Rounds 5-8 found
  real defects every time, and nearly all were ONE class: half two abolished the shared CI
  workspace, and I corrected the comments describing it in the places I was looking and not in the
  places I was not. SIX separate instances, surfaced across four rounds, each time by a reviewer
  rather than by me. In one round I introduced a fresh defect while fixing the previous one — a
  string replace that spliced a sentence and left a dangling "HERE" inside the paragraph about the
  opposite code path. The lesson is not "the reviewers are thorough"; it is that a sweep done from
  memory instead of by `grep` across the whole tree always leaves residue, and this branch is the
  evidence.

## scope-auditor
VERDICT: PASS
risks_checked:
- Confirmed the delta is exactly what the brief claims: `tests/test_persist_docs_policy.py`'s diff touches only the docstring text — the assertion `jobs == ["data:build:main"]` and its preceding logic are byte-identical. No new test, no changed selector, no changed behaviour.
- Checked the `scope_paths` addition of `tests/test_persist_docs_policy.py` against the doc-sync rule already established for `layering.md` / `profiles.example.yml` / `docs/operations_guide.md` in earlier rounds: it is a sixth instance of the same stale "shared ci_* workspace" claim that half two abolished, corrected under the same authority, in-branch, by the same amendment. Consistent application, not a scope grab — it touches no new code, only a comment describing a fact this branch itself changed.
- Checked the RECURRING COST correction in `decisions_taken`: it retracts the prior false "query volume unchanged" claim, names the mechanism (three incremental fact models lose `{{ this }}` on an MR's first pipeline under per-MR datasets and full-build instead of merge), and gives a measured magnitude bound (ci_core 0.7 GB → sub-cent per pipeline). A correction to an already-declared threshold item, not a newly-surfaced undeclared mechanism.
- Checked `decisions_reserved` and `protected_override` for any quiet reopening or silent new decision riding along with these two prose fixes — found none; both are unchanged in substance from the prior passed state.
- Checked for any code/YAML/SQL hunks accompanying this delta beyond the two named changes — none found.

## cto-reviewer
VERDICT: PASS
risks_checked:
- **Delta size vs. my earlier PASS** — the diff since is prose in `contract.md` plus one docstring in `tests/test_persist_docs_policy.py`. No flag, no target derivation, no assertion and no profile line moved, so the basis of the earlier pass (the `--favor-state` asymmetry, the `DBT_CI_TARGET` derivation, both halves of the isolation pin) is intact and a delta judgement holds.
- **Cost declaration vs. what ships** — checked the query-volume claim against the code rather than the sentence. `materialized='incremental'` returns exactly three files — `3_core/fct_fixture_team_stats.sql`, `fct_fixture_player_stats.sql`, `fct_fixture_event.sql` — the same three the declaration names, and `is_incremental()` keys on `{{ this }}`, which `--defer` never redirects. A fresh `ci_mr<IID>_core` does mean a FULL build on an MR's first pipeline whenever `state:modified+` reaches one of them. The declaration now matches the mechanism being built; "query volume is unchanged" is gone.
- **Magnitude method** — the declaration sizes the full-build from the OUTPUT dataset (`ci_core` 0.7 GB) where BigQuery bills bytes SCANNED (upstreams, single-digit GB). A proxy, understating by a small factor — at EU on-demand rates a few GB is still ~1–2 cents per affected pipeline, so the CPO-facing conclusion ("small, not zero, plus wall time") survives. Approximate method, no material misstatement, not a finding.
- **Storage accumulation is monotone and unbounded** — no expiry, by an explicit CPO instruction quoted verbatim in `escalations.log`. The measured base (6.0 GB full set, ~12¢/month) and the fact that nothing self-deletes are both in front of him, and the earlier false "self-deletes" description is retracted in both the contract and the log. Bounding is filed, not silently absorbed. Accepted with authority.
- **Guard authority** — `.gitlab-ci.yml` is in `scope_paths`; `protected_override` names a real CPO approval quoted verbatim in the diffed `escalations.log` ("do as recommended", then "fix it"), and `impact_map` is a genuine guard trace, not a placeholder.
- **Guard invariant direction** — CI must fail CLOSED and still does: the singular selection is byte-identical, no `allow_failure`, no `|| true`, nothing conditional, `data:build:main`'s `--target prod` gate untouched. The change moves which database the gate reads, not whether it can fail.
- **New mechanism (A3)** — no new job, stage, script, runner or package; half two exports one shell variable and reuses the untouched `macros/generate_schema_name.sql`. Even read strictly as a mechanism it carries the CPO's "fix it" verbatim.
- **Credentials / permission widening** — the heredoc changed from `<<'EOF'` to unquoted `<<EOF`, the one credential-adjacent edit, so I read the whole anchor body rather than trusting the comment saying it was checked: `$` appears only in `${DBT_CI_TARGET}` (three occurrences), no backticks, no backslashes, both outputs `method: oauth` with no keyfile. Unquoting cannot splice an environment value or a command substitution into the written profile. WIF untouched; no IAM change in the diff and none needed (`roles/bigquery.user` already grants `bigquery.datasets.create`).
- **Undeclared thresholds** — both crossings the diff makes (recurring cost, and the arguable mechanism) are declared with authority. `decisions_reserved: none` no longer reserves what the same commit ships.
- **The docstring delta itself** — the rationale for excluding `data:build:mr` from `dbt docs generate` is corrected, not weakened: the assertion is unchanged and the reason it gives is now stronger.

## platform-reviewer
VERDICT: PASS
risks_checked:
- **Both named delta fixes verified in the files, not the prose about them.** `tests/test_persist_docs_policy.py` now reads "that merge request's own `ci_mr<IID>_*` datasets", quotes the superseded wording, and states the rejection reason is unchanged; the file is in `scope_paths` and the extension is under `amendments:`. `contract.md` RECURRING COST no longer contains "query volume is unchanged". I checked that claim against the warehouse rather than accepting it: `materialized='incremental'` appears in exactly three models, matching the three named, and `{{ this }}` is resolved in the current target and never a `defer_relation`, so a fresh `ci_mr<IID>_core` does make the first pipeline full-build.
- **Guard direction, read from the code.** `data:build:mr`'s `dbt test` still exits non-zero on failure; no `allow_failure`, no `|| true`, no `when:` change, selection untouched, suite size unchanged. CI stays fail-CLOSED.
- **Deferral semantics traced rather than trusted.** dbt resolves a `ref()` to the deferred relation only when `favor_state` is set OR `get_relation()` finds nothing in the current target, and `defer_relation` is set only for nodes NOT selected. So on the build line `--favor-state` affects only unselected upstreams (the documented build-then-revert residual is exactly right), and on the test line, where nothing is selected, removing it is what makes the suite read the branch. dbt-bigquery's `list_relations_without_caching` swallows `NotFound`, so an MR whose first pipeline has no `ci_mr<IID>_*` datasets defers cleanly to prod instead of erroring.
- **Test coverage of the changed behaviour, both halves, verified against the helpers.** `_script_lines_by_job` resolves the `*dbt_profile` alias into `data:build:mr`'s lines, so the `export DBT_CI_TARGET=...CI_MERGE_REQUEST_IID...` derivation is genuinely visible to the assertion, and `_script_lines` reaches `dataset: ${DBT_CI_TARGET}` through the same alias. Each of the five reverts named in `done_when` lands on an assertion. Not happy-path-only.
- **Pre-existing guards that could have been silently broken by this edit.** `test_ci_writes_the_dbt_profile_where_sqlfluff_looks_for_it` regexes `cat\s*>\s*(\S+)/profiles\.yml`; the unquoted `<<EOF` leaves it matching, and the profile is still written at script step 0 in every job that later invokes dbt/sqlfluff. No parity test binds `.gitlab-ci.yml` to the dormant `.github/workflows/ci-data-build.yml`, correctly left unedited.
- **Duplicated enforcement.** Checked `scripts/cleanup_orphan_relations.py`, the repo's only drop mechanism: `ALLOWED_DATASETS` is an explicit prod list, so `ci_mr<IID>_*` is unreachable by construction and "nothing here deletes anything" holds against the one script that could contradict it.
- **Re-run and interruption safety.** `mkdir -p`, `export` and `cat >` are idempotent; `dbt seed`/`build` create the dataset if absent and use create-or-replace / MERGE, so a job killed mid-build leaves no half-written table. GitLab concatenates `script:` items into one shell, so the `export` really does reach the later dbt lines.
- **Remaining stale-claim sweep, done independently of the builder's.** Live hits are the corrected files, the frozen `.github/workflows/`, two tests whose `ci_marts` references are still true, and `docs/roles/platform_reliability.md:87` — which names the CI/prod dataset hazard, a different and separately fixed question, correctly out of scope.
- **One thing I looked at and waived.** The YAML comment states the residual's frequency as build-then-revert while `contract.md` names two paths (adding rebase-onto-an-absorbing-main). The rebase case still ends in the state the comment describes, so the comment is loose, not false, and "rare" holds on either path. Below the bar for a FAIL.

## analytics-engineer-reviewer
VERDICT: PASS
> Verdict carried forward from the previous hash: this reviewer's territory (`dbt_project/**`) is
> byte-identical since it was given. The only changes after it were `tests/test_persist_docs_policy.py`
> and contract prose, neither under `dbt_project/`.
risks_checked:
- `.gitlab-ci.yml` full file swept for `ci_analytics`/`ci_marts`/`shared ci`/`target: ci` — the one surviving `ci_marts.mart_team_season_insights` hit is inside a past-tense reproduction record, not a claim about current behaviour. No comment asserts the shared/`ci_analytics` workspace as present-day fact.
- `dbt_project/docs/layering.md` — the target table and both `⚠` paragraphs now describe `ci_mr<IID>` as the CI target and state explicitly "there is no shared `ci` target"; the prose is past-tense when describing the retired one.
- `dbt_project/profiles.example.yml` — retains a literal `ci:` block for readability but is explicitly labelled reference-only with "there is no shared `ci` target in CI", and the `dataset:` comment reads "in CI this is ci_mr<IID>".
- Both dbt guard CI notes rewritten; remaining `--favor-state`/"shared" mentions are explicitly framed as the superseded rule being corrected, and both state "There is no shared `ci` target any more."
- `macros/generate_schema_name.sql` is byte-unchanged (absent from the patch) and its logic matches the claim exactly: prefix by `target.name` when a custom schema is set, bare `target.schema` when not. Cross-checked against `dbt_project.yml`: `2_base` sets no `+schema` and seeds carry none, so base models and seeds genuinely ride the profile's `dataset:` line. With `target.name = ci_mr114` and `dataset: ${DBT_CI_TARGET}` this yields `ci_mr114_marts/_core/_staging/_intermediate` plus bare `ci_mr114`.
- Verified the pin's substring checks (`"--target ci"` vs `"$DBT_CI_TARGET"`) do not false-positive against `--target "$DBT_CI_TARGET"`, and that `_script_lines` really does see the profile body through the alias.
- Same-window / metric-catalogue coverage semantics unaffected: no model SQL, no ratio, no seed row touched.

## escalations
(none)
