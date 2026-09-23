# Acceptance evidence — German is measured like the other two languages

Read from a fresh `npm run build` on the committed sample (1,329 pages; `audit-seo: 1330 built
page(s) checked. OK.`; `check-built-pages: … OK.`) on `fix/german-coverage`, branched from `main`
at `db70ab1d`. Exit codes read bare.

criteria_demonstrated:
  - THE CHECK RENDERS GERMAN BY DEFAULT AND SAYS WHERE IT DOES NOT.
    `python scripts/check_design_inventory.py --dist site_v2/dist`, no `--langs` flag:
    `20 pages · 2 viewports · 3 languages (pages per language: en 20, de 7, fi 20) · 94 renders ·
    0 failures · 0 warnings`, exit 0. Before this change the same command read
    `2 languages · 80 renders`. The 14 added renders are the 7 built rows × 2 viewports.
    The parenthetical is READ FROM THE RENDERS THAT HAPPENED, not from what was requested, so no
    page can hide inside the language count. Round 1 FAIL from the platform reviewer: the first
    version computed it from the configured page list, which left `--page` ad-hoc targets — always
    English only — counted as covered in every requested language. Checked on all four shapes:

    | run | reported |
    |---|---|
    | full, three languages | `3 languages (pages per language: en 20, de 7, fi 20) · 94 renders` |
    | mocks only, three requested | `3 languages (pages per language: en 1, de 0, fi 1) · 2 renders` |
    | ad-hoc `--page` only, three requested | `3 languages (pages per language: en 1, de 0, fi 0) · 1 renders` |
    | one language, uniform coverage | `1 languages · 1 renders` — no caveat, correctly |

    A language that reached no page shows as `0` rather than vanishing from the tally, which was
    the precise hole in the first attempt.
  - THAT SUMMARY IS PINNED BY A TEST, NOT BY THIS FILE. Round 2 FAIL from the platform reviewer:
    the caveat was the code that had just been wrong, and no test ran the check with more than one
    language, so a regression to the round-1 bug would have turned nothing red — the only evidence
    was the transcripts above, which CI never re-runs. `test_the_summary_names_a_language_that_did
    _not_reach_every_page` now runs the check as a subprocess on an ad-hoc page with `--langs
    en,de,fi` and asserts `pages per language: en 1, de 0, fi 0`, and again with `--langs en`
    asserting no caveat at all. SEEN RED against the round-1 computation (restricting the tally to
    languages that rendered something): `AssertionError: 1 pages · 1 viewports · 3 languages ·
    1 renders` — the caveat gone and the line claiming three. Restored: `37 passed`.
  - GERMAN IS ACTUALLY MEASURED, NOT MERELY COUNTED. A count in a summary is not a measurement,
    so the German page was broken on purpose and the check run against it. Injecting
    `<style>.sechead .eyebrow{font-size:11px !important}</style>` into
    `dist/de/bundesliga/index.html` only — English and Finnish untouched — gives exit 1 and:
    `FAIL  Competition overview · 375 · de · Block heading [.sechead .eyebrow #1] · expected font-size=13px · measured 11px`
    `FAIL  Competition overview · 700 · de · Block heading [.sechead .eyebrow #1] · expected font-size=13px · measured 11px`
    `1 pages · 2 viewports · 3 languages · 6 renders · 2 failures · 0 warnings`
    Both failure lines carry `de` and no `en`/`fi` line appears. The script restored the file and
    verified the restore byte-for-byte; `dist` is build output and is not tracked.
    ⚠ Run BEFORE this change, the same break is invisible: the German file is never opened.
  - THE LANGUAGE SETS CANNOT DRIFT APART AGAIN.
    `python -m pytest tests/test_design_inventory.py -q` → `36 passed`. The new pin,
    `test_the_check_renders_every_locale_the_site_publishes`, reads `LOCALES` out of
    `site_v2/src/lib/href.ts` and compares it with `DEFAULT_LANGS`. SEEN RED against the value
    that shipped for the whole life of this check:
    `At index 0 diff: 'en' != 'de'` / `Right contains one more item: 'fi'` — 1 failed.
    Restored and green again; `git diff` on the script shows only the three intended hunks.
  - THE GERMAN SEARCH TEXT IS THE SITE'S OWN WORD, EVERYWHERE.
    `grep -rl "Teams, Spieler suchen" site_v2/dist | wc -l` → `0` across 1,330 pages; the built
    German pages read `Mannschaften, Spieler suchen…`. `python scripts/check_copy_gate.py` →
    `690 strings across 3 locales`, exit 0; `check_ui_i18n_metrics.py` exit 0;
    `cd site_v2 && npm test` → 101 passed.
  - THE LONGER WORD COSTS NO LAYOUT. Measured in headless Chromium on the built German page, with
    the previous string swapped back into the same box so the two readings differ only by the word:

    | viewport | `.searchbox` before | after | clipped | page scrollWidth before → after |
    |---|---|---|---|---|
    | 375 px | hidden | hidden | — | 375 → 375 |
    | 700 px | hidden | hidden | — | 728 → 728 |
    | 1024 px | 182 | 227 | no | 1024 → 1024 |
    | 1280 px | 182 | 227 | no | 1280 → 1280 |
    | 1440 px | 182 | 227 | no | 1440 → 1440 |

    The box grows 45px and nothing moves off the page. German (227) is now the widest of the
    three; English is 180 and Finnish 192. The 700px overflow (728 of 700) is the pre-existing
    header one, identical before and after, and is not this branch's.
    ⚠ Worth knowing and NOT fixed here: `.searchbox` is hidden at both viewports the check
    measures, so no viewport the gate renders would ever have caught a search-box defect. Out of
    this task's scope; named on the MR head.
  - NO LIVE DOCUMENT THE CONTRACT MAY TOUCH STILL SAYS "EN AND FI".
    `grep -rn "EN and FI" docs/ design-mocks/ .claude/skills/` → nothing describing this check.
    `.gitlab-ci.yml`'s `validate:ui` comment still does and is knowingly left: the file is a
    protected governance path, the contract gate refuses the edit without a CPO-approved
    `protected_override`, and a comment does not justify loosening a guard. On the MR head.
