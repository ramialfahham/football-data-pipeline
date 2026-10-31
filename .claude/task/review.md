# Review — feat/222-teams-page — 2026-10-31

diff_sha256: f767fdb3b689fcb29476ca74d0a63130b80c210d60591afceecfaf114252481d

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged path is in scope_paths, including the two spec-kind files and the rendered evidence added by amendment; the trimmed sample (778 of 3,342 rows, unchanged) carries its recorded approval.
- The copy, the doc text, the page kind, the export bytes and runs, and the .gitlab-ci.yml edit each carry a recorded approval; decisions_reserved is none.
- Added comments and docs carry no dates, issue numbers or chat quotes.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The export only projects, renames the crest and lifts national_teams_first; it computes no ranking, affiliation or mapping.
- The confederations join cannot fan out (unique key), and null regions or places are skipped, never sorted as NaN.
- The page sorts only by served places; teams and countries sharing a place keep the export's order, pinned by node tests.
- A test pins fetch_team_index's join and its name order.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every rendered field is in the export's keep list and the committed sample; every new copy key exists in EN, DE and FI.
- Filters hide whole lists, headings, groups and blocks together, so fold counts stay true.
- Lists are one grid of at most two columns, 6 shown (10 for top lists); rows link only to built team pages.
- The rendered evidence states its method, widths and the filter swaps.

## platform-reviewer
VERDICT: PASS
risks_checked:
- teams_index is in the deploy export's --entities list and in ENTITY_TYPES; the export writes deterministically.
- The teamIndex kind is in both the schema enum and ENTITY_VALUES, which a test holds equal.
- The page reads team payloads from disk, as the Team page does; no payload is bundled.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The .gitlab-ci.yml change is one line, deploy:export's --entities list, and protected_override names its approval.
- The export's recurring cost (about 20 MB billed per manual deploy) and the page kind are recorded as approved.
- No dependency, permission or guard invariant changes.

## escalations
(none)
