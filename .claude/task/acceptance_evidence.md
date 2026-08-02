# Acceptance evidence — #846

The five criteria are the CPO's, approved 2026-08-02 ("all 5 approved") and locked. Each is
restated verbatim, then shown. Two are demonstrated from BUILT site output, two from the test
suites, and one is honestly split: its warehouse half cannot run locally.

criteria_demonstrated:

  - **1. "A player who played a summer tournament still opens on their club season."** Shown at the
    payload level, which is where the defect lived.
    `tests/test_export_site_data.py::test_shape_player_payload_opens_on_the_featured_club_season_not_the_latest`
    feeds two real rows — `WC 2026` (the more recent) and `PL 2025` — and asserts the payload's
    top-level identity comes from the club row (`position == "D"`, the club season's modal position,
    not `"M"` from the national squad) while the WC season is still served in `seasons[]`. Passing.
    ⚠ HALF PENDING: that the MART flags the club row for the real M. Rogers needs
    `mart_player_profile` rebuilt, and a local `dbt build` would clobber the shared prod dataset. It
    is demonstrated from `ci-data-build` on the PR, not here. The rule it rests on is
    `entity_type = 'club'` first, then `domestic_league`, then most recent year.

  - **2. "Nothing a visitor sees on a team page changes."** Shown from BUILT output, as a
    before/after of the same page. Built `main`'s version (changes stashed), copied all three
    locales out of `dist/`, restored, rebuilt, and diffed:
    `diff before_<lang>.html dist/<lang>/teams/manchester-united/index.html`
    -> de: IDENTICAL · en: IDENTICAL · fi: IDENTICAL.
    Byte-identical in every locale, which settles geometry, ordering and every string at once, since
    none can differ if the bytes do not. Corroborating counts in the built `en` page, before and
    after: `Premier League` x10, `2025/26` x3. It is identical rather than merely close because the
    flag was set on the row the old `.find()` returned, and the warehouse rule that produces the
    flag is the rule the page used to apply.

  - **3. "The opening season is decided in one place instead of three."** All three copies are gone,
    verified by search rather than by claim: `grep -n "_latest_season_row" scripts/export_site_data.py`
    -> no matches (function removed); `grep -n "latest\.get\|latest\["` -> no matches; `[team].astro`
    no longer contains `.find((s) => s.competition_type === ...)` and instead reads
    `team.seasons.find((s) => s.is_featured_season)`. The export now REFUSES to choose:
    `test_featured_season_row_refuses_to_choose` asserts it raises both when no row is flagged and
    when two are, so a mart shipped without the column fails loudly instead of silently falling back
    to recency. Passing. The player page's own copy is not converted here and cannot be: it lives in
    `stash@{0}`, held on #845. The mart half it needs IS included.

  - **4. "If the rule ever breaks, a test catches it before a reader does."**
    `dbt_project/tests/assert_one_featured_season_per_entity.sql` counts flagged rows per entity
    across BOTH profile marts and returns any entity whose count is not exactly 1, so it fails on
    none and on two. Registered, verified with the project venv dbt:
    `dbt ls --select test_type:singular` -> `football_data_pipeline.assert_one_featured_season_per_entity`.
    Plus `not_null` on the column itself in `shared.yml` for both marts, and `not_null` +
    `accepted_values` on `entity_type`, the column that scopes the rule to club football.
    ⚠ It EXECUTES against data in `ci-data-build`; `dbt ls` proves it is wired, not that it passes.

  - **5. "The change does not quietly alter anything else."** `site_v2/src/data/teams/33.json`: 24
    seasons, every one gained `is_featured_season` and nothing else. Exactly one is `true` —
    `PL 2025` — which is the row the old rule selected, which is why criterion 2's diff is empty.
    Verified by parsing the built file: `seasons: 24`, `flagged: [('PL', 2025)]`,
    `all have the key: True`, `exactly one: True`. No other committed sample needed the field:
    `git ls-files site_v2/src/data` returns four files, and neither `fixtures/1492306.json` nor
    `competitions.json` contains a `seasons` array.

## The missing-flag path, measured

The non-null assertion in `[team].astro` removes the old `?? team.seasons[0]` fallback. Tested, not
assumed: flipping the sample's one flagged season to `false` and rebuilding gives
`Cannot read properties of undefined (reading 'league_code')` and `exit 127`. The BUILD fails and a
visitor never sees it, because the pages are statically generated. Fail-closed in the right
direction. The sample was restored and the byte-identical diff re-run afterwards to prove the
experiment left nothing behind. Full detail in `rendered_page_evidence.md`.

## Suites and gates run locally

- `python -m pytest tests/test_export_site_data.py` -> **41 passed** (39 existing, 2 new).
- `cd site_v2 && npm test` -> **59 passed**.
- `npm run build` -> 9 pages, 3 team pages across 3 locales, `audit-seo: 10 built page(s) checked. OK.`
- `python -m sqlfluff lint <both marts + the new test> --templater jinja --dialect bigquery` from the
  repo root, full rule set -> **All Finished!** (clean).
  ⚠ `mart_player_profile.sql` also reports `TMP`/`PRS` and `ST11` under the jinja templater. Those
  are PRE-EXISTING, not from this change: the file uses `dbt_utils.generate_surrogate_key`, which
  the jinja templater cannot resolve, and the unparsable section cascades into bogus "unused join"
  findings. Confirmed by linting the file as it stands on `main` and getting the same output. CI
  lints with the dbt templater, which resolves it.
- `dbt parse` -> clean, 94 models. `dbt ls --select mart_team_profile+` and `mart_player_profile+`
  still return only themselves, so no accidental downstream dependency was introduced.

## Not demonstrated here, by design

Criterion 1's warehouse half and criterion 4's execution both need the marts rebuilt. dbt shares the
CI and prod datasets, so a local build would clobber production. Both are demonstrated from
`ci-data-build` output on the PR.
