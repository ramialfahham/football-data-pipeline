# Acceptance evidence — Competitions hub: build the approved design (#144)

criteria_demonstrated:
  - EVERY ROW IS A LINK TO ITS COMPETITION'S PAGE. `CompetitionIndexGrid.astro` renders the row as
    `<a class="comp-row" href={localeHref(lang, slug + "/")}>`; `slug` is a served column of
    `mart_competition_index` on all 48 rows of `competition_index.json`. Dev server `/en/competitions/`:
    `document.querySelectorAll('a.comp-row[href]').length` → **48**, first three hrefs
    `/en/belgian-pro-league/`, `/en/ligue-1/`, `/en/serie-a/`; `/de/competitions/` in a background
    tab → **48**. Production build (`npm run build`): `dist/en/competitions/index.html` carries 48
    `<a class="comp-row"`, `dist/fi/competitions/index.html` 48 distinct `/fi/{slug}/` hrefs; the
    build's `audit-seo` checked 307 pages OK, so every href resolves to an emitted page
    (`[competition]/index.astro` builds one per row). Hover/active/focus rules for `a.comp-row`
    mirror `a.brow`; `.comp-name`/`.comp-region`/`.comp-meta` are `display: block` spans inside the
    anchor (measured `display: block` on `.comp-name`).
  - THE COLLAPSE DECIDES FROM THE FILTER STATE. Each radio now carries a `value` (`""` for All,
    `club`/`national`, the confederation code); the script reads the two checked values and hides a
    group when no row's `data-entity-type` / `data-confederation` matches both. `offsetParent` is
    gone from the source and from `dist/en/competitions/index.html` (0 occurrences). Dev server,
    driven through the real `change` events: National teams → Continental championships, World Cup,
    National team qualifiers shown, the other five hidden; Africa → Continental club cups,
    Continental championships, National team qualifiers shown; Clubs + Africa → only Continental
    club cups; Clubs + Oceania → all eight hidden (no OFC club competition is onboarded); All/All →
    all eight shown. Background load: `/de/competitions/` opened in a tab that was never fronted
    (`document.visibilityState === "hidden"`) → `hidden: [false ×8]`, 48 links — the case that
    hid all eight groups on 2026-09-14.
  - EVERY KIND IN THE SEED HAS THREE LANGUAGES, AND A GATE HOLDS IT. `strings.ts` gains
    `compTypeDomesticSuperCup`, `compTypeClubQualifying`, `compTypeIntercontinentalSuperCup`,
    `compTypeClubFriendlyDomestic`, `compTypeClubFriendlyInternational`,
    `compTypeNationalTeamFriendly` in EN (verbatim from the seed's `label_en`), DE and FI.
    `check_copy_gate.py` check 5 reads `competition_types.csv` and `confederations.csv`
    (`label_i18n_key`) and requires each key in all three locales: `COPY GATE ok: 495 strings …
    21 seed label keys resolvable in every locale`. MUTATION shown red twice: one DE key renamed
    → 3 findings (checks 2 and 5); one key deleted from ALL THREE locales → 3 "seed key
    unresolvable" findings (check 2 silent, check 5 the only catcher). Tests in
    `tests/test_governance_hooks.py`: `test_copy_gate_fails_on_a_seed_key_no_locale_carries`
    (a fixture seed publishing a key no locale has → `main() == 1`),
    `test_copy_gate_passes_when_every_seed_key_resolves` (blank cells skipped, resolvable keys pass),
    `test_copy_gate_reads_the_real_seeds` (both seed paths, ≥14 and ≥7 keys, all resolvable),
    `test_copy_gate_fails_closed_on_a_seed_without_the_key_column` (a seed whose header lacks
    `label_i18n_key` → the reader raises and `main()` prints `FAIL: cannot read the seed label
    keys` and returns 1; an absent seed file → the same; a cp1252-saved seed (a decode error, not an
    OSError) → the same; never zero keys, never a traceback — platform round-1 and round-2
    findings, each shown red against the previous reader: 1 failed);
    with check 5 disabled in the gate (`seed_keys = {}`) the first FAILS (1 failed); restored, 10
    copy-gate tests pass (11 with the fail-closed test). `check_ui_i18n_metrics.py` and `check_layer_contract.py` green; `ruff check . --config .ruff-ci.toml` (CI's lint) all checks passed.
  - THE WIREFRAME AND THE OVERVIEW POINT AT #128. `docs/wireframes/08_browse.md` opens with the
    authority block (#128 wins; what it changed: row links, filter-state collapse, all kinds in
    three languages, the country in the reader's language via #69, no country hubs); §6's "Rows
    are NOT links, on purpose" is struck and replaced; §7's collapse paragraph says the script
    reads the filter state and why `offsetParent` failed. `docs/wireframes/00_overview.md` row 08
    reads "Competitions index", **built**, **approved on GitLab #128**, with "country hubs … still
    pending" struck (in no menu, no issue).
