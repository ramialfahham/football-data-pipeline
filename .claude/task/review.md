# Review — feat/dbt-docs-pages — 2026-07-03

> G3 Lock artifact. Publish a public dbt docs lineage site by folding it into the EXISTING GitHub Pages
> deploy: one `dbt docs generate --static` step (continue-on-error) in pages-match-preview.yml, a `-f`-guarded
> copy of target/static_index.html into _site/dbt-docs/ in build_match_preview_site.sh, and one README link.
> The workflow is a PROTECTED path; the contract carries a protected_override tracing to the CPO's plan
> approval (hazy-imagining-pascal.md, approved unchanged via ExitPlanMode). Required set (routing):
> **scope-auditor (always) + cto-reviewer (.github/workflows/** + scripts/**)**. Round 1 (hash 2ca0b37a) —
> BOTH PASS.
>
> **Rebound onto post-#642 main** (2026-07-03) after sibling PR #642 (README "Design decisions") merged
> first: only the `.claude/task/*` scratch files conflicted (resolved to this task's versions); README
> auto-merged (the dbt-docs link + #642's section coexist). The workflow/script/README code hunks are
> BYTE-IDENTICAL to the r1 review — only contract.md's diff BASE shifted (#641 → #642), so the hash
> re-anchored 2ca0b37a → cdfcbbae. Both r1 PASS verdicts carry unchanged (same content).

diff_sha256: cdfcbbaee4bc5d182cfa5a6f12caba20c95f7fa135ac476439902407df4b30f0

## scope-auditor
VERDICT: PASS  (round 1)
risks_checked:
- Protected-override + scope integrity: .github/workflows/** is PROTECTED; the contract's protected_override
  is present, names the exact file, quotes the CPO "do it" -> ExitPlanMode plan approval (hazy-imagining-
  pascal.md, which explicitly lists this workflow), and matches scope. Every staged file is within scope_paths
  (.github/workflows/pages-match-preview.yml, scripts/build_match_preview_site.sh, README.md, .claude/task/**);
  no EXISTING workflow step (deps/seed/run/test/export/deploy) or existing script logic was altered — additive
  only. The §10 "new workflow step" was pre-approved in the plan; the diff matches the plan exactly.
- Silent docs-failure / incomplete deploy (checked, held): continue-on-error on the docs step + the `if [ -f ]`
  copy guard mean a docs-generation failure cannot block the app deploy but would leave /dbt-docs/ absent on
  Pages. Bounded by contract (docs are best-effort): the link is new (no prior users), the daily schedule
  retries, and dbt docs generate is mature. No regression to the match-preview path.

## cto-reviewer
VERDICT: PASS  (round 1)
risks_checked:
- Flag/output correctness for dbt 1.7.2: dbt-bigquery==1.7.2 pins dbt-core 1.7.x, and `dbt docs generate
  --static` (bundling manifest+catalog into a single target/static_index.html) is a real 1.7+ feature — the
  flag and the output filename copied by the script match. If it were wrong the step would no-op under
  continue-on-error and the -f copy would skip, degrading gracefully (docs absent, app unaffected).
- Regression isolation + placement/auth: the step sits after the existing dbt seed/run/test, so BigQuery WIF
  auth, profiles.yml and packages are already in scope (dbt docs generate self-compiles, needs nothing more).
  Exactly one continue-on-error in the file (scoped to the new step); the `[ -f ]` guard is set -euo pipefail
  safe; no existing step/script line changed; no new trigger or cadence (same schedule + push paths), one
  extra catalog metadata query per existing build. Non-blocking note: catalog covers the whole project graph,
  so the published lineage may include relations not built in this job — expected/acceptable for best-effort docs.

## escalations
(none)
