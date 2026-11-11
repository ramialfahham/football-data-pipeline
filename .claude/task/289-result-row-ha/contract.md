# Task contract — the Result row's two-line form on phones

objective: >
  Issue #289. A result row takes its two-line form whenever its list does not fit on one line: line
  1 is chip · score · crest · opponent, line 2 is home or away · competition · date, and a middle dot
  travels with the item after it. The stacked match header loses the line between its two teams.

refs: >
  #289; the Result row on phones approved in chat, 2026-11-11, recorded on #289; scope and criteria
  approved in chat, 2026-11-11.

scope_paths:
  - .claude/task/289-result-row-ha/
  - site_v2/src/components/fixture/RecentMatch.astro
  - site_v2/src/components/player/PlayerRecent.astro
  - site_v2/src/styles/system.css
  - site_v2/src/lib/fitBlocks.mjs
  - site_v2/src/lib/fitBlocks.test.mjs
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/fixtures/chart_screenshots/

protected_override: >
  docs/design/components.yml: the Result row's rule and its meta part's rule state the two-line form
  by fit, and the line-2 home or away class is registered, approved in chat, 2026-11-11, recorded on
  #289.

impact_map: >
  writers: none in the warehouse.
  lineage: no dbt model and no export change, so no lineage moves.
  consumption: RecentMatch.astro draws the Match page's Recent matches (SplitSection's two .rcol
  columns, each fitted as its own list; their subgrid keeps row by row level) and the Team page's
  matches (TeamMatches.astro, [team].astro); PlayerRecent.astro draws
  the Player page's Recent matches. Both add home or away at the start of line 2, shown only in the
  two-line form; the one-line form keeps it after the name. fitBlocks.mjs marks these lists fit-one
  or fit-two with its existing "rows" measure, as it already does for the Player page's list; the
  Result row's 420px container switch gives way to that mark. Head to head and goal rows keep
  their 420px switch. The system.css rules on `.resrow .pill` and `.resrow .rscore` set both to the
  first line. The header rule is `.mp .mast .team` under 700px, the Match page only.
  guard: docs/design/components.yml is read by scripts/check_component_registry.py, which writes
  the block standard's Elements table, and by scripts/check_design_inventory.py through that table.
  The row, meta, wide and narrow texts change; one class part is added with a one-line, 12px muted
  assertion; the Fitted block rule's selector names the result lists; the component's narrow key
  stays at w420, which its Head to head and goal rows still use.
  blast_radius: measured on main 0953e41c's build with the change injected (DE, Match page Recent
  matches): home or away on a line of its own falls to 0 at 280 and 560px; rows in a list that does
  not fit on one line take two lines, and at under 320px line 2's items may wrap between items.

acceptance_criteria:
  - In the two-line form, home or away starts line 2, in every result row on the Match, Team and Player pages, at every width from 280 to 1010px, in English, German and Finnish.
  - The result chip and the score sit on the row's first line, at every width.
  - A result row in the one-line form looks as it does today.
  - Under 700px, the Match page header shows the two stacked teams without a line between them, upcoming and played.
  - No result row exceeds two lines, except where the opponent's name or line 2's items wrap between words or items, at any width.

approved_design:
  - match: #132
  - team: #134
  - player: #136

decisions_taken: >
  The two-line form is the one approved in chat, 2026-11-11, recorded on #289; the one-line form is
  unchanged. The switch by fit reuses fitBlocks.mjs's "rows" measure, the Player page's mechanism.
  No new mechanism. The sitewide middle-dot rule is #231 and stays out of this task.

decisions_reserved:
  - none: the form is approved on #289.

done_when:
  - The offline gates pass and npm test passes, with fitBlocks.test.mjs pinning the result-row lists.
  - Every result row on the branch build, at 280–1010px in 10px steps in EN, DE and FI, has 0 home or away on a line of its own, 0 chips below the first line, none sticking out, and no row over two lines except by a wrap of the name or of line 2's items between words or items; one-line rows keep main's positions.
  - The local design check on the Match, Team and Player pages gives no FAIL or COUNT line above main's baseline.

amendments:
  - 2026-11-11: criterion 5 also excepts a wrap of the opponent's name, in a row under 320px wide —
    authority: approved in chat, 2026-11-11; content: a long name wraps between words, never cut off.
  - 2026-11-11: criterion 5 allows the name and line 2's items to wrap between words or items at any
    width — authority: approved in chat, 2026-11-11; content: a long competition name wraps line 2
    in rows 320–420px wide too.
  - 2026-11-11: the Result row's wide summary and narrow form in components.yml state the by-fit
    condition beside the meeting and goal rows' 420px switch, its line-2 home or away part carries
    the never-split assertion, and the Fitted block rule's selector names the result lists —
    authority: the approval recorded on #289; content: the registry's text matches the rows.
  - 2026-11-11: criterion 4 stands over the #132 mock, which draws a line under the first stacked
    team; the mock is corrected in a later change — authority: approved in chat, 2026-11-11;
    content: under 700px the Match page header shows the two stacked teams without a line.
  - 2026-11-11: + tests/fixtures/chart_screenshots/ — authority: approved in chat, 2026-11-11;
    content: comparison-en-dark-375.png and comparison-en-light-375.png and their manifest hashes
    are replaced with CI's Linux renders; the stacked header's lost line moves the block up 1px,
    so three anti-aliased pixels on one bar edge change in each.
