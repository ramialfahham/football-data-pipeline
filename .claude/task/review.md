# Review — feat/39-nightly-cloud-run — 2026-08-09

diff_sha256: 9017de88cfdd1da18e190ba2eebc1640ede83988c258818ea16a760a19f832c5

rounds: 3

<!--
Round history, stated plainly because every FAIL was the builder's:
  r1  scope-auditor FAIL · cto-reviewer FAIL · platform-reviewer FAIL
  r2  cto PASS · platform PASS · scope-auditor FAIL (same item, second form)
  r3  scope-auditor PASS
`cto-reviewer` is NOT routed to these paths by .claude/review_routing.json — no row covers
`Dockerfile` or `deploy/**`. It was spawned deliberately because this change declares a NEW
MECHANISM and a RECURRING COST, which are its thresholds and which no routing row can find.

HONEST NOTE ON THE HASH: cto and platform returned PASS at round 2 against a diff that differs
from this one by exactly one addition — the `.gitattributes` block appended to
`.claude/task/escalations.log` to cure scope-auditor's round-2 finding. That addition is a
record of a ruling both had already read cited in `contract.md`, and touches neither reviewer's
territory. Stated rather than glossed, because the hash binds all three verdicts to the final
diff and only scope-auditor saw it.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Verified the round-2 defect (CPO authority for `.gitattributes` unverifiable — absent from `escalations.log`) against the new log content at `.claude/task/escalations.log:1838-1854`: the "SCOPE EXTENSION, asked and granted mid-task" block now records the question as put, the verbatim CPO answer, the demonstrated failure mode, the declined alternative, and the round-2 FAIL that prompted the entry — cured.
- Cross-checked `contract.md:129-146`'s amendment text against the new log block for consistency (same quote, same declined alternative, same rationale) — no divergence between the two artifacts.
- Confirmed nothing else in the branch changed since round 2 (contract.md unmodified, `scope_paths` and `impact_map` untouched) — the delta is confined to the single log addition, within bounds for a delta re-review.
- (r1, still standing) Scope conformance: every changed file maps to a `scope_paths` entry; no out-of-scope file touched.
- (r1) Secrets sweep across the full diff: no key, token or password material. `.env`, `*.pem`, `*.key`, `*credentials*.json` are excluded from the image by `.dockerignore`; the API key is referenced only by name.
- (r1) Threshold declarations: NEW MECHANISM and RECURRING COST both declared in `contract.md` and corroborated in `escalations.log`, with `cto-reviewer` spawned outside normal routing. Declared, not smuggled.
- (r1) Parity claim in `impact_map`: hand-diffed the entrypoint's step order against `.gitlab-ci.yml` `data:nightly` (667-711) — same steps, same order, same gate; `.gitlab-ci.yml` itself untouched as the contract requires.
- (r1) `decisions_reserved` (deletion of `data:nightly`, ingest/dbt job split, Stages 2-3, sharding): none decided in the diff.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 finding (project-scoped `roles/run.invoker` on `github-actions-dbt@…`) — cured. `deploy/nightly/README.md` now binds resource-scoped via `gcloud run jobs add-iam-policy-binding fdp-nightly --region europe-west1`, and names the project-scoped form as rejected with the reason. Grepped the whole repo for `run.invoker` / `projects add-iam-policy-binding`: the only other occurrence is explanatory prose describing what was rejected — no leftover project-scoped binding anywhere.
- `contract.md`'s `credentials:` paragraph now enumerates BOTH grants, states grant 2 is resource-scoped, and records that the earlier draft under-counted them; matches the runbook and matches the IAM bullet in `escalations.log`.
- Whether the delta grants any capability beyond the CPO record: reviewed all nine file diffs — no new dependency, no additional grant, no widened permission beyond the two declared IAM bindings. `requirements.txt` unchanged.
- CPO authority for the new mechanism: traced through `contract.md` `decisions_taken` and the 2026-08-09 `escalations.log` entry — a real, sequenced approval ("start with #39" → "plan stage 1" → plan approval), with region and Secret Manager attributed to the CPO directly.
- Recurring cost: ~$1.70/month falling to ~$0.35, cross-checked against the log's independent restatement and against the alternatives the CPO explicitly ruled out (buying minutes, the OSS programme, reduced cadence). Proportionate, not silently absorbed.
- Boring-technology check: Composer/Airflow, Dataflow/Spark and a self-hosted runner are each named and rejected with reasons in `escalations.log` before landing on Cloud Run Jobs — a standard building block, not an exotic choice.
- Guard paths: none of the nine appear in this diff, confirmed against the file list, so `protected_override` and opus-routing do not apply.
- Secrets: no credential literal introduced; the API key is read from Secret Manager at runtime, never hardcoded.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 finding 1 (IAM grant) — cured; resource-scoped binding confirmed in `deploy/nightly/README.md` §3, with `contract.md` and `escalations.log` both enumerating the two grants.
- Round 1 finding 2 (decoration test) — cured. The regex-order test is gone; `_run_entrypoint` now EXECUTES `deploy/nightly/entrypoint.sh` under real `bash` with `python`/`dbt` replaced by logging stubs on PATH. Hand-traced the named regression against `entrypoint.sh:36`: rewriting the condition to `|| true` makes the script always take the early-exit branch, so `test_new_data_runs_the_full_prod_build` loses all six asserted steps from the trace and fails exactly as claimed. `test_a_quiet_night_exits_before_dbt` alone would NOT catch it — both branches skip dbt when `new_data=false` — which is why the pairing is what closes the gap, and both are present.
- Decoration hunt on the replacements: named a concrete single-line edit that flips each red (remove the `exit 0`; drop a contract check; drop any of the six steps; change a target flag). Neither is vacuous.
- Whether the stubs could mask a real failure: they observe invocation and argument strings only, not `cwd` or real dbt/BigQuery behaviour. Inherent to a parity/gate test rather than a new hole, and backstopped by the separate static tests pinning the target string and the shipped profile's target set.
- The "protected path" rewording in `README.md` and `entrypoint.sh`: confirmed the phrase is gone (satisfying the `test_governance_doc_parity` sweep) and confirmed via `.claude/hooks/task_contract_gate.py` that `.gitlab-ci.yml` genuinely is in the guarded set — so the replacement wording stays factually accurate rather than weakening the claim.
- `.dockerignore` correctness: verified every runtime-read path (`docs/competition_registry.yml`, both `scripts/check_*.py`, `dbt_project/**` except target/dbt_packages/logs, `requirements.txt`, `ingestion/**`) is NOT excluded, while secrets are.
- `.gitattributes` `*.sh`/`Dockerfile` → `eol=lf`: a real fix for the CRLF-shebang failure mode, consistent with the CPO-authorised amendment.
- Credential hygiene across `Dockerfile`, `.dockerignore`, `profiles.yml`, `README.md`: no secret values; the API key is sourced from Secret Manager at runtime only.

## escalations
(none)
