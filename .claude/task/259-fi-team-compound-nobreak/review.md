# Review — fix/fi-compound-nobreak — 2026-11-15

diff_sha256: d676b931b9964d346ce1bd319a250b57de4c1249638cde14ad3ad44a66ef4e34

rounds: 4

rounds_cap_override: round 3 findings were a missed selector, fixed; the CPO approved a 4th round, approved in chat, 2026-11-15.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 4: every file outside the task folder is in scope_paths (helper, its test, playerPage.ts, PlayerComparison.astro, components.yml, block_standard.md).
- docs/design/components.yml carries protected_override naming the CPO approval of 2026-11-14; the contract carries rounds_cap_override for this round.
- No new mechanism, no recurring cost, no wording, metric or URL change; the one-word and non-Finnish outputs are pinned by the test.
- The components.yml rule and its block_standard.md row carry identical selector and rule text.
- The round 3 legend selector `.cmp-p .chart-legend` is in both files and exists in ChartLegend.astro and system.css.
- The impact_map grep matches the repo: three files reference teamBeforeCompound.
- No secret, no workflow or permission change.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Selector coverage from source: teamBeforeCompound is called twice, both in PlayerComparison.astro; the intro renders as `p.bsub.cmp-p` and the legend as `.cmp-p .chart-legend`; no other render site.
- Helper traced against wholeWords.mjs: the no-break space and U+2011 leave "-pelaajaan," unwrapped; one-word names and en/de unchanged.
- Rule text accurate and identical in components.yml and block_standard.md; measured kind unchanged.
- rendered_page_evidence.md states honestly that check_design_inventory.py was not run and what was measured instead.
- No metric, label, value or data file touched.

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanism: the helper follows the existing src/lib/*.mjs plus node --test pattern; not a new mechanism.
- No dependency, no cost change, no secret.
- Guard invariant: the rule gains two selectors and loses none; CI still fails closed.
- protected_override names a dated CPO approval; impact_map is filled with real content.
- The selector is not language-limited, so en and de are measured too; the first clause of the rule already applies to any team name.
