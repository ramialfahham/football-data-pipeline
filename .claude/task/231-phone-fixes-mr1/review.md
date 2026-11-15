# Review — claude/231-phone-fixes-mr1 — 2026-11-15

diff_sha256: 18520d0512d8e83c142c830afcacbea0a1f19c3089b82f8a4799b1906e8d19dd

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3 re-asked once inside the round after a one-line fix: the Match page is named in approved_design (match #132), since the venue change reaches it through Masthead.astro; the finding closed with no other change.
- Every changed file is in scope_paths; the Players hub and nation pages, the pin file, Breadcrumb.astro and the registry line each carry a dated "approved in chat" amendment; components.yml carries protected_override.
- impact_map downstream and blast_radius state the Breadcrumb change (Home kept on a two-level trail under 700px) and match the one-condition diff; trails of three or more levels are unchanged.
- decisions_reserved (the Player club link and the Teams league heading link, cause 4b) is untouched; no new mechanism, cost or credential.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed on an empty trail under 700px on the two-level pages and missing rendered evidence; round 2 read the Breadcrumb condition `far: (i === 0 && items.length > 2) || last` and every caller's item count, and found the round-1 finding closed with no new one.
- Trails of three or more levels, the Matches day variant and the scroll script are unchanged; no text, field or metric is added or removed.
- rendered_page_evidence.md names its tool and what it observed; the three hub pages other than Teams are marked as read from markup, not measured.

## platform-reviewer
VERDICT: PASS
risks_checked:
- tests/test_phone_fixes_231.py: the crumb pattern now catches both ways of writing the class and a test feeds it both plus a non-crumb nav; the two-level test covers the Competitions, Teams, Players and Matches trails; each test fails on revert.
- wholeWords.mjs keep(): traced by hand against the node tests, no double-wrapping or nesting; the lowercase/digit/double-space test title now matches its input.
- baseline.json banned_properties for system.css 7 to 6 matches a recount of the pattern in check_page_css.py against system.css; the pin only goes down.

## cto-reviewer
VERDICT: PASS
risks_checked:
- docs/design/components.yml changes one line, the Breadcrumb's narrow form, under a protected_override naming the file, the change and the approval date; no other registry part changes.
- The registry line matches Breadcrumb.astro and the system.css comment; no new mechanism, dependency, cost or guard invariant.

## escalations
(none)
