# Review — claude/social-prematch-template-952145

diff_sha256: c39e68be8af057cfe67cc1420aa473fd04b7d77ffba1435cbef3a1496dd391eb

rounds: 3
rounds_cap_override: approved in chat, 28 Nov 2026

## bi-analyst-reviewer
VERDICT: PASS
findings:
- [nit] share with no visible volume: design-mocks/social/prematch.py metric rows "Schüsse aus dem Strafraum" and "Ballbesitz" — no total beside the share; the approved design has none
- [nit] metric names differ from the site's: design-mocks/social/prematch.py "Schüsse aufs Tor gegen" and "Abschlussquote" — the site's German strings name them differently; the approved image uses these
- [nit] window coverage: design-mocks/social/prematch.py "Letzte 5 Pflichtspiele" — a match in a competition the registry does not load is absent and the run cannot see it
- [nit] next-match guard: design-mocks/social/prematch.py model() — an earlier match in play when the mart was built can leave a later one flagged next
- [nit] no fit check: design-mocks/social/prematch.py screenshot() — content too tall would be clipped and the run would still succeed
risks_checked:
- The percentage path multiplies as a float and then rounds, in the order of the site's formatter; the 23/40, 1/8 and 5/8 cases read correctly.
- One point reads "Punkt" and a level goal difference reads "0", as on the Match page.
- The queried columns exist in the three marts and in mart_competition_index.

## fixes
- Formatting differs from the Match page on edge values | sweep: every number the image prints (points word, goal difference, percentages, per-match averages); fmt() compared with the site's formatter on 501,500 shares and 2,168 averages, 0 differences | test: tests/test_social_prematch.py::test_an_exact_half_rounds_up_as_on_the_match_page

## escalations
(none)
