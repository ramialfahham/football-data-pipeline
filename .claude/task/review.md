# Review — chore/retire-dead-pages-triggers — 2026-06-13

> Issue #422 (audit F13): remove six dead per-competition staging path triggers
> (pl/pd/bl2/sa/l1/vl) from .github/workflows/pages-match-preview.yml. Protected path —
> protected_override (CPO "Option 1 granted", 2026-06-13). Required reviewers for
> .github/workflows/**: scope-auditor + cto-reviewer. Both PASS first iteration.

diff_sha256: 1cd28110bd28c1ca2d2447c01ccdeda7170c89ad8f5fa5c15145a37647306efb

## scope-auditor
VERDICT: PASS
risks_checked:
- Protected-path authorization: the contract carries a protected_override quoting CPO
  approval 2026-06-13 ("Option 1 granted"), specific to #422 and to editing
  .github/workflows/pages-match-preview.yml — dated, contemporaneous, not a blanket grant.
  Only the declared scope_paths are touched; no other protected file.
- Behaviour-preserving + scope discipline: the generic "dbt_project/models/1_staging/**"
  trigger remains and subsumes the six removed per-competition globs (which are strict
  sub-paths), so no push that previously triggered the deploy is now missed; the per-competition
  staging dirs are forbidden by the zero-file rule (check_layer_contract.py) and don't exist,
  so the triggers were permanently dead. The diff removes ONLY those six lines — other
  stale-looking triggers (retired wc_supporting_league_codes.csv seed, stale mart paths)
  were left untouched (they belong to #430), no scope creep.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Trigger subsumption / no missed-trigger regression: GitHub Actions path globs are OR-based;
  each removed glob (1_staging/api_football/{pl,…}/**) is a strict sub-path of the surviving
  generic "1_staging/**" (line 12), so every push the six could have matched is still covered.
  No behaviour change to which pushes fire the deploy.
- Dead-trigger verification + structural integrity + guard safety: Glob of
  1_staging/api_football/ shows only flat files (no pl/pd/bl2/sa/l1/vl subdirs);
  check_layer_contract.py hard-fails CI if any per-competition staging subdir appears, so the
  triggers are structurally guaranteed dead. The six contiguous lines were removed cleanly;
  the rest of on.push.paths and the whole workflow (jobs, the permissions block contents:read /
  id-token:write / pages:write) are byte-for-byte unchanged; no credentials/secrets in the diff;
  protected_override authority recorded.

## escalations
(none — both reviewers PASS first iteration. Behaviour-preserving workflow-config cleanup;
no CI run needed to prove data correctness — the change only removes permanently-dead trigger globs.)
