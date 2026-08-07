# Acceptance evidence — copy gate defects (GitLab #7)

Four criteria, drafted by the builder and approved by the CPO on 2026-08-06 before any code, then
LOCKED. Criterion 2 was amended once, on a clean tree, with the ruling recorded in the contract's
`amendments:` — the bar did not move (0 em dashes in shipped values before and after the
amendment); only my mis-drafted wording, which had counted code comments, was corrected.

Each criterion is restated verbatim, then shown. Criteria 1, 2 and 4 are demonstrated from
command output; criterion 3 is shown twice — mechanically against `HEAD`, and from BUILT `dist/`
output, because a dropped placeholder is only user-visible once rendered.

criteria_demonstrated:

  - **1. "`python scripts/check_copy_gate.py` exits 0 and prints no findings."** Demonstrated.
    Before this branch, on `main` at `c701ecc`, the gate exited **1** with **16** findings. After:

    ```
    $ python scripts/check_copy_gate.py; echo "exit=$?"
    COPY GATE ok: 354 strings across 3 locales (300 chrome + 54 metric labels),
    381 corpus strings consulted
    exit=0
    ```

    Note the count is the gate's own: 354 strings across three locales, checked against the
    381-string validated corpus. It is not a pass over zero strings — the gate carries a
    `MIN_KEYS` floor precisely to make that impossible, and it did not trip.

  - **2. "Zero U+2014 EM DASH characters in shipped string VALUES — the gate's own scope. Code
    comments are not shipped copy and are out of scope."** (as amended). Demonstrated over the
    342 double-quoted dictionary values in `site_v2/src/i18n/strings.ts`:

    ```
    string values scanned: 342
    values containing an em dash: 0
    values containing an en dash (substitution check): 0
    ```

    The en-dash count is included deliberately. The approved fix restructures each sentence — a
    trailing clause becomes a full stop, a parenthetical becomes appositive commas,
    `aboutWithH2h` takes a colon. Substituting U+2013 would have read identically to a user and
    merely evaded the check, which is the "never loosen a guard" failure wearing a different
    costume. **Zero were introduced**, so the restructuring is real rather than cosmetic.

  - **3. "Every changed string keeps its placeholder tokens exactly — the multiset of `{...}`
    tokens per key is identical before and after."** Demonstrated twice.

    (a) Mechanically, against `git show HEAD:site_v2/src/i18n/strings.ts`, for all three locale
    copies of each changed key:

    ```
    ok aboutWithH2h      occurrences: 3  placeholders: ['{away}','{home}','{meetings}','{record}','{round}']
    ok comingPerformance occurrences: 3  placeholders: []
    ok comingSquad       occurrences: 3  placeholders: []
    ok heroVerdictUnder  occurrences: 3  placeholders: ['{deserved}','{gap}','{sotd}','{team}']
    ok heroVerdictOver   occurrences: 3  placeholders: ['{deserved}','{gap}','{sotd}','{team}']
    ok secForm           occurrences: 3  placeholders: []
    ok footerDataSource  occurrences: 3  placeholders: []
    ok key set unchanged: 96 distinct keys
    placeholder/key drift: 0
    ```

    The key-set check is included because a copy edit that silently drops a key would leave a
    locale short and is exactly what check 2 of the gate exists to catch.

    (b) From BUILT output. `npm run build` in `site_v2/` completed green — `npm test`, the
    `check-page-specs.mjs` gate and the `seo-audit` step all passed, 9 pages built in 5.41s. Six
    rendered pages, both page types, all three locales, with comments/script/style stripped so
    only reader-visible text is counted:

    ```
    ok en/teams/manchester-united/index.html                                 em_dashes=0 unresolved=[]
    ok de/teams/manchester-united/index.html                                 em_dashes=0 unresolved=[]
    ok fi/teams/manchester-united/index.html                                 em_dashes=0 unresolved=[]
    ok en/brasileirao/matches/2026-07-26-palmeiras-vs-atletico-mg/index.html em_dashes=0 unresolved=[]
    ok de/brasileirao/matches/2026-07-26-palmeiras-vs-atletico-mg/index.html em_dashes=0 unresolved=[]
    ok fi/brasileirao/matches/2026-07-26-palmeiras-vs-atletico-mg/index.html em_dashes=0 unresolved=[]
    rendered failures: 0
    ```

    `unresolved=[]` is the criterion's real point: a dropped placeholder renders a literal
    `{sotd}` to a reader. None does.

    **LIMIT ON THIS EVIDENCE, stated rather than glossed.** Three of the changed keys —
    `comingTitle`, `comingPerformance`, `comingSquad` — do **not** appear in the built output in
    any locale, so (b) demonstrates nothing about them. They are referenced by **no component**:

    ```
    $ grep -rn "comingPerformance\|comingSquad\|comingTitle" site_v2/src --include=*.astro --include=*.ts
    site_v2/src/i18n/strings.ts:69,70,71    (en)
    site_v2/src/i18n/strings.ts:220,226,227 (de)
    site_v2/src/i18n/strings.ts:373,374,375 (fi)
    ```

    Nine hits, all of them the definitions themselves, zero consumers. They are dead strings,
    left behind when the Performance and Squad tabs gained real implementations
    (`TeamPerformance.astro:71` branches on `hasBench`, not on a coming-soon placeholder).

    They are still fixed here, because `check_copy_gate.py` reads every dictionary value
    regardless of whether a component uses it, so criterion 1 cannot pass while they carry em
    dashes. Their evidence is (a) and criterion 1 only. **Deleting them is out of scope for this
    MR** — removing user-visible copy definitions is a §10 call and belongs in its own change.

    Recorded honestly: a first pass reported one em dash per page. It was inside the inline
    theme-toggle `<script>` — a JavaScript source comment, never displayed. The measurement was
    wrong, not the page; the check above strips `<script>` and `<style>` and the count is 0.

  - **4. "`fi.secForm` uses the `kunto` root, matching the validated corpus (`kuntojakso` in
    site/i18n/fi.json)."** Demonstrated in source and in rendered output.

    ```
    site_v2/src/i18n/strings.ts:314:  secForm: "Kuntovertailu",

    fi.secForm rendered           'Kuntovertailu': 1
    fi.secForm old value          'Muotovertailu': 0
    ```

    This closes a deferral that was explicit in the file: the comment at `strings.ts:421-422`
    recorded that `secForm` carried the same `muoto`/`kunto` error as the SEO title fixed under
    #867 and was **not** corrected then because it was "shipped copy he has not ruled on". The
    CPO ruled on it 2026-08-06; that comment is updated rather than left contradicting the code.

    The sibling Finnish change is shown by the same run:

    ```
    fi.footerDataSource rendered  'Tietolähde: API-Football': 1
    fi.footerDataSource old value 'Data: API-Football'      : 0
    ```

## Not claimed

- **No GitLab pipeline has run on this branch.** These are local results. The MR pipeline is the
  authority and its URL belongs here before merge.
- **The gate is still wired into nothing.** That is deliberate and is PR 2's job. This PR only
  makes `main` clean enough that wiring it does not turn the default branch red.
- **`scripts/check_copy_gate.py` advertises an exemption it does not implement** — its message
  offers "the value needs a comment saying so", but check 4 parses no comment. Found while
  satisfying criterion 1. Not fixed here; it belongs to the MR that wires the gate.
