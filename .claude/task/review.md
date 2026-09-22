# Review — fix/menu-statistics — 2026-09-22

diff_sha256: 3653d084dc8d2e15b27a051b1d750a1db4c08871643ee3ce92428ee3d3d35b3c

rounds: 1

One round, both required reviewers PASS. The scope-auditor's only finding was a stale line
number in the contract's own impact map (`10_home.md:999`, actually 1002), corrected and
confirmed in a one-line delta. The bi-analyst read that same citation the other way; checked
directly afterwards — `grep -n "Leaderboards page exists (#139)"` returns 1002, so the contract
as it stands is right.

## scope-auditor
VERDICT: PASS
risks_checked:
- All three words trace to a dated CPO quote in `refs` ("the CPO on !217's thread, 2026-09-22"), which is what a §10 user-visible naming decision requires; the builder's earlier drafts were overridden, not defended.
- Superseding a prior ruling is recorded in place: `10_home.md:9-13` now carries the chain (Stats → Leaderboards on #127 → Statistics today, with the reason), rather than the old text annotated beside the new.
- The hub/label distinction was applied in both directions: `site_architecture.md:247`, `north_star.md:115`, `10_home.md:1002` and `gen_navmap.py:155` still read Leaderboards (the page, the milestone, the export payload); every six-item menu list reads Statistics. Neither over- nor under-swept.
- `grep -rn "navLeaderboards"` across `site_v2/`, `docs/`, `design-mocks/` returns zero live hits.
- Dead text preserved: the two component hunks swap the key and add no `href`; `audit-seo` unaffected.
- Every touched path is in `scope_paths`; `north_star.md` is correctly absent from both the diff and the list, because it must not change.
- No credential-shaped content, no new mechanism, no recurring cost.
- Delta: the contract's line-number citation corrected; no code, scope or decision field touched.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Swept `docs/wireframes/**`, `site_v2/src/**`, `design-mocks/gen_navmap.py`, `site_architecture.md`, `ui_design_brief.md` and `north_star.md` in both directions rather than trusting the claim: every menu-label site moved, every hub-name site stayed — including `00_overview.md:139`'s `05_leaderboards.md` page reference, which this task correctly leaves alone.
- Exactly one `navStatistics` definition per locale; no orphaned `navStats` or `navLeaderboards` outside the task artifacts; `gen_navmap.py` derives the label from the header and the strings, so no second place can drift.
- Chrome labels are exempt from the field-binding rule by `09_chrome.md` §3 (fixed product IA, not registry- or mart-driven), so there is no fabricated field here; no metric, catalogue or percentage concern.
- Dead text preserved: only the key swap in both components, `href` null at every measured width and locale.
- The evidence files are this branch's and honest about method — a built-`dist` sweep plus headless-Chromium DOM and geometry at 375/700/1280 in three locales, stated as such rather than as a screenshot claim, with the pre-existing 700px sideways scroll disclosed rather than omitted.
