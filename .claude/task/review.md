# Review — fix/menu-leaderboards — 2026-09-22

diff_sha256: 5d2b04ba0bfd7ff2e03ff3c875bc2a6eb57c51b3fc0e56aa1f8c483518fe5e4a

rounds: 2

Round 1: the bi-analyst FAILed. The impact map swept for the KEY name (`navStats`), which appears
in no prose, so five places that write the menu out in words still said "Stats" — four in
`09_chrome.md` itself (the quote, both ASCII diagrams, the States bullet) and the
`site_architecture.md` line that document cites as its authority. Round 2 swept by the concept:
those five plus `north_star.md` and `ui_design_brief.md`, which carry the same list. Both
reviewers PASS on the delta.

## scope-auditor
VERDICT: PASS
risks_checked:
- The English word is the CPO's: both quotes verified verbatim in the repo — `10_home.md` ("the menu item Stats is renamed Leaderboards") and the #127 approved-design section as the tracker carries it ("Stats is renamed Leaderboards (menu, footer, milestone 7, issues #139/#140)"). Not paraphrased, not the builder's.
- The German and Finnish words are in `decisions_reserved`, drafted for the MR head — consistent with §11 (a code decision is recorded by the MR the CPO merges), not a silent §10 naming decision.
- The key rename `navStats` → `navLeaderboards` is internal identifier hygiene with its reason in `decisions_taken`; no stray old key anywhere live.
- Every file in the cumulative patch is in `scope_paths`; the three documents added in round 2 are each a single-word substitution inside a pre-existing nav list, matching the round-1 finding and the amendment's authority. In scope, not creep.
- The §6 States bullet's surrounding claim ("every non-brand item is inert") was already false — Competitions became a link when its index shipped under #128 — so correcting it in the sentence being edited is a doc-sync fix of an already-decided fact, not a second change; site behaviour is unchanged.
- No `href`, route, page or link-graph change in the diff; `audit-seo: 1195 built page(s) checked. OK.`
- No credential-shaped content, no new mechanism, no recurring cost, no cadence change.
- `docs/tracker/gitlab_snapshot.md`'s remaining "Stats" is correctly untouched: script-generated, hand-edits hook-blocked, refreshed at session end.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: `09_chrome.md` half-renamed (module-bindings table updated, the quote at line 19, both ASCII diagrams and the States prose left saying "Stats"), and `site_architecture.md:222`, the line that document cites as authority, likewise. Round 2: all four locations and the cited line verified fixed in the patch, not only the working tree.
- The rewritten States bullet introduces no fresh inaccuracy: its "Competitions is the one link" claim checked against `SiteHeader.astro` — `navCompetitions` carries an `href`, the other five including `navLeaderboards` do not.
- The item is still dead text: `SiteHeader.astro` renders it as a `<span>` with no `href`, `SiteFooter.astro` the same, at every width in every locale per the rendered evidence.
- The copy as language: "Bestenlisten" is the standard German compound for a leaderboard list and reads as a nav label; "Kärkilistat" matches the "Kärki" stem already validated on Home (`Kärkipelaajat`, `Kärkijoukkueet`) and is distinct from the separate DE "Rankings" ruling on the competition tab. No defect in either draft.
- The evidence files are this branch's and honest — method named, drawer state at 375px measured, the pre-existing sideways scroll flagged as pre-existing.
- Swept `docs/**` independently for the same stale nav list rather than trusting the claim: the only remaining hit is the script-owned tracker backup, outside the territory and not hand-editable by rule.
