# Review — feat/219-home-rebuild — 2026-10-18

diff_sha256: 25a979daf2d069c8361618042c11f76c4701adc1f9edfe89b1b43663a511b2da

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: docs/site_architecture.md:276 still named core.dim_team and region_rank; round 2 checked the Landing row against fetch_landing_payload's reads and the scope amendment with its authority, no defect.
- Checked every file in the diff against scope_paths and the dated amendments, each with a named authority.
- Checked the six acceptance criteria against #219's What exactly, identical word for word.
- Checked §10: the crest, the board rows, the 1-7 rank, UTC with its zone and the doc texts are all in decisions_taken; no product, naming or metric decision outside it.
- Checked system.css reach: .fxmore is used by HeroFixtures and MatchesDay only, and MatchesDay's fold renders unchanged, so approved_design home: #127 holds.
- Round 3: checked .pre-commit-config.yaml's --maxkb=1024 against its scope amendment and the CPO approval it names; no other hook changes, no secret guard narrowed.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: a hairline between a date heading and its first match in 3 of 23 folds (system.css:610); round 2 checked the summary-adjacent selector and the in-browser measurement, no defect.
- Checked the built EN/DE/FI Home: 8 boards of 7 rows in catalogue order and format, both intros p.bsub, localised fold labels, Top match tags and date headings, crest/name/chevron heads.
- Checked the binding rule: every landing.json field is emitted by the export from marts or the catalogue; no field exists only in the sample.
- Checked HeroFixtures applies no order of its own and no orderUpcomingGroups, FixtureRow, LandingFixture or region_rank reference remains in site_v2/src.
- Checked no naked percentage, no fabricated zero, no new metric, existing i18n keys only.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Checked fetch_landing_payload selects and joins only, ordered by the served competition_order then fixture_order; the Python sort is gone.
- Checked competition_order is unique per competition and fixture_order unique within a competition's next round, so the order is deterministic.
- Checked the inner join to mart_competition_fixtures cannot fan out (fixture_sk unique) and is_match_that_matters is carried from mart_next_matchday.
- Checked the meta overlay: the crest from _competition_page_meta is set last and a null crest stays None; region_rank is no longer emitted.
- Checked the Matches page and competition payload shapes are untouched, and the board format and per_match come from _board_catalogue.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the competition crest wiring had no test; round 2 checked the hero test now fails if the loop, the logo_url key or the per-competition scope breaks.
- Checked the .gitignore allowlist expands to exactly the 537 tracked upcoming ids, plus 11 force-tracked played samples, and admits no id outside the set.
- Checked 34 team payloads and 50 days match the allowlist and the README.
- Checked the three pin tests are equality pins lowered only for the rewritten files.
- Checked no dependency, credential, guard-path, hosting or new third-party origin change.
- Round 3: checked the --maxkb=1024 arg reaches the overridden entry, the check still fails closed above 1 MB, and CI's pre-commit run only checks added files, so already-committed payloads are unaffected.

## escalations
(none)
