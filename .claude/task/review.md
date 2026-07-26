# Review — feat/826-page-spec-contract — 2026-07-26

diff_sha256: 2a2620dbfdf340c482892dcded8abd0a634fa8d3a3517bd177859c3d3a69e405

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Fixture spec block→mart mappings comply with documented relationships in content_architecture.md; the mislabeled "Single fixture" block is removed, `mart_team_momentum_window` correctly folded into "Form (recent)" per row 73 ("+ `_window` drill-down"); all marts referenced across both committed specs verified to exist under dbt_project/models/5_marts/**.
- i18n key extraction regex handles packed multi-key lines and hyphenated key formats via the widened pattern `[A-Za-z0-9_-]+`, locked by dedicated regression tests, and guarded by a self-check floor that fails loudly if EN-dict extraction drops below 50 keys.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Cross-referenced every mart name in both committed specs against the real filesystem (all 11 exist) and confirmed the round-1 fabricated "Single fixture" block is genuinely gone from the diff; every listed i18n key exists in the real EN dict, none fabricated.
- Verified the build-gate mechanism actually fires on both real build paths (read ci-site-v2.yml and deploy-site-v2.yml directly: both run `npm run build`, which triggers `prebuild`); verified the two round-1 findings are actually fixed (schema/checker relationship reworded accurately in contract + doc + file comment; check-page-specs.test.mjs exists with 14 real tests including a non-vacuous schema/checker cross-check); confirmed no guard-path touch, no new dependency, correct fail-closed polarity, and re-run/interruption safety by construction (pure read-only script).

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round-1 fix verified directly against the diff: the fabricated "Single fixture" block is fully removed; `mart_team_momentum_window` is correctly folded into "Form (recent)" and traced to its real field (`form_window`) in `export_site_data.py`, matching content_architecture.md row 73.
- Every mart and i18n key in both spec files traced to real, existing bindings (mart files on disk, i18n keys in the EN dict, several spot-checked against the actual component code that renders them); block names verified verbatim against content_architecture.md §3; confirmed the diff carries no rendering-affecting site_v2/src/** change, so rendered_page_evidence.md is correctly not required here.

## escalations
(none)

---

### Round 1 (superseded — kept for the audit trail)

Round 1 hash: `3a67b88455421deea371cbf7ad748c84567d82ab62c354533a599ccfbaa526d3`

- **scope-auditor**: PASS (scope compliance, mart/i18n existence, no §10 violations; two non-blocking
  fragility notes: the i18n-key regex charset and the Layout-import regex path-coupling).
- **cto-reviewer**: FAIL — (1) objective/docs implied the checker validates against
  `page-spec.schema.json` at runtime; it doesn't. (2) no automated regression test existed for the
  checker itself.
- **bi-analyst-reviewer**: FAIL — `fixture.spec.json`'s "Single fixture" block was mislabeled:
  bound to `mart_team_momentum_window` (which is really "Form (recent)"'s drill-down mart per
  content_architecture.md row 73), while the real "Single fixture" mart
  (`mart_team_fixture_stats`/`mart_player_fixture_stats`) names a capability that isn't built on
  this page.

**Fixes applied between rounds**: reworded contract.md/content_architecture.md/the checker's own
comment to state plainly the checker hand-rolls rules rather than loading the schema file; added
`check-page-specs.test.mjs` (14 tests, Node's built-in `node --test`, zero new dependency) including
a schema/checker cross-check test, wired into `prebuild` via a new `test` script; refactored the
checker to export its functions and guard the `main()` invocation; widened the i18n-key regex to
allow hyphens; added a "0 real pages found" abort guard; removed the fabricated "Single fixture"
block from `fixture.spec.json` and folded its mart into "Form (recent)" where it belongs. Contract
amended (clean-tree stash-dance) to widen `scope_paths` from the single checker filename to
`site_v2/scripts/**` to cover the new test file — authority: cto-reviewer's own round-1 finding.
