# Task contract — the design checks the new header needs (part 2 of 3)

objective: >
  Issue #362, part 2 of 3: the design checks measure what the approved header and the pages in
  the fan's time zone will show, before the site changes. The rendered check also renders built
  pages at 520px, joins a Pages row named "(continued)" to its page and counts no hidden row as a
  Fold or a score; the component registry check admits the logo's one green token.

refs: >
  #362 (header design approved in chat, 27 Nov 2026, recorded on the issue). #365 (the name and
  the wordmark with its green, approved in chat, 27 Nov 2026). Part 1 is the marts and the export,
  part 3 the site.

scope_paths:
  - .claude/task/362-b-design-checks/
  - scripts/check_component_registry.py
  - scripts/check_design_inventory.py
  - scripts/parts_page.py
  - tests/test_check_component_registry.py
  - tests/test_design_inventory.py
  - tests/test_merge_ready.py

protected_override: >
  scripts/check_design_inventory.py and tests/test_design_inventory.py: a full run also renders
  every built page at 520px, the width the approved header shows its search field at (approved in
  chat, 27 Nov 2026, recorded on #362), and no mock page at that width; the tests fail a mock a
  full run renders at 520px, a built page it does not, and a presence need keyed on a page that no
  longer expects its element. At 520px a built page no Pages row owns is measured like any other,
  except that the finding "no inventory element measured on this page" is not repeated there; a
  test holds that a page a row owns still reports it. The check joins a Pages row named
  "(continued)" to its page, two
  rows with one address still fail otherwise, and a hidden neighbour-day row counts for neither a
  Fold nor a score. --pages selects a page together with its continued row. In a full run the only
  render the check may lack is a mock page at 520px; any other missing render stops it. The test
  of the one two-width exemption also holds that a second rise beside it is still reported. Other
  test edits, none of which drops a check: the red run of the lint lowers the pin of CSS outside
  system.css in MetricRow.astro, the red run of the rendered check reads the search field's width
  from the inventory, the rows that must show the header's search and the rows a presence need
  names are read joined, and new tests cover the join, the --pages selection and the planning of
  the real Pages table. No pin rises.

impact_map: >
  Both checks run in validate:ui and in test:python on every merge request that touches the site
  or the checks; no pipeline file changes. No hook reads DEFAULT_VIEWPORTS (grep over scripts,
  .claude/hooks and tests): its readers are scripts/merge_ready.py full_widths(), which expects a
  full sweep's log to name those widths, and tests/test_design_inventory.py and
  tests/test_merge_ready.py. check_chart_screenshots.py imports only serve from
  check_design_inventory.py; parts_page.py imports check_component_registry.py. The mock pages
  keep the widths their pins were measured at, so baseline.json does not change. A run that names
  its widths with --viewports renders every page at each of them. join_continued only joins a row
  whose name ends " (continued)" and repeats its page's kind, source, URL and FI mode; any other
  pair of rows stays two rows, so two rows with one address still fail. The Pages table on main
  has no such row. The presence check now counts only rows without the hidden attribute; no page
  on main hides a match row. check_component_registry.py admits the custom property --logo-green,
  and its fill only in a rule whose whole selector is `.brand .logo .pv` and that starts the
  stylesheet or follows a closing brace; the stylesheet on main declares no such token.
  If either check were wrong, a layout or a colour outside the sets could merge unmeasured.
  Nothing reads the warehouse and nothing deploys.

approved_design:
  - none: no page output changes

depends_on:
  - none: no merge request is open

shared_files:
  - none: no design baseline or chart screenshot changes in this part

decisions_taken: >
  520px is the width the approved header shows its search field at (approved in chat, 27 Nov 2026,
  recorded on #362), so the rendered check measures the built site there. That mock pages are not
  rendered at 520px is an engineering call: their gap counts are pinned per page over the other
  widths, the added width adds renders of the same gaps to them, and a pin never rises; no mock
  draws a breakpoint there. That a page no row owns does not repeat the "nothing measured" finding
  at 520px is an engineering call of the same kind: the root index.html, which only sends a visitor
  to a language, holds no inventory element, and its pin counts that once per measured width; no
  check that main runs changes. The wordmark's green is approved in chat, 27 Nov 2026, recorded on
  #365; the coordinating session's call is that it is one logo-only token, that --accent stays and
  that the component registry check admits this one token in the logo's rule only. A Matches
  page's days in the fan's zone follow the kick-off rule on #362, so a hidden row of a
  neighbouring day is not what the page shows. The "(continued)" row is an engineering call: it
  lets a long Pages row be split in part 3 without a second page in the plan. Part 3 writes the
  520px width and the "(continued)" row into block_standard.md, which needs two reviewers of its
  own and so cannot ride in this part. The parts page no longer places the header part part 3
  removes; until then it lists that part without a kind. No dependency and no recurring cost; a full sweep renders each built page one width more. The header work is split
  into three merge requests because one branch needed four reviewers and a branch may need two
  (working_agreement section 2).

decisions_reserved:
  - none: the design is approved on #362 and #365; questions go to the coordinating session.

done_when:
  - python scripts/ci_local.py --mr is green.
  - The full rendered design check (built pages at seven widths, mock pages at six) passes on the site as it is on main, with no pin raised and baseline.json unchanged.

amendments: (none)
