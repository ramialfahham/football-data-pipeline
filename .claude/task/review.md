# Review — feat/144-competitions-hub-approved-design — 2026-09-14

diff_sha256: 597a745cd0191e24ebe3dc8939dd8f50ec89fb36f290a42aceb34292caaa4f98

rounds: 4
rounds_cap_override: round 4 is a two-word docstring fix after CI (`test_no_decision_history_in_code.py` flagged two dates in the round-3 commit's docstrings); no standing FAIL by review; the CPO did not rule on the cap — the override practice of !172–!174.

Rounds are per reviewer. Round 1: scope-auditor PASS, bi-analyst-reviewer PASS,
platform-reviewer FAIL (two findings in the copy gate's new check: a renamed `label_i18n_key`
column read as zero keys and passed; an absent seed file raised a bare traceback). Round 2
(platform only; fix + test): FAIL on one residual — the `except (OSError, KeyError)` let a
non-UTF-8 seed or a malformed CSV escape as a traceback. Round 3 (platform only; `except
Exception`, cp1252 test case): PASS. Round 4 (platform only, haiku): CI's comment-history test
flagged two dates in docstrings of the round-3 commit; both replaced with "when the check was
added"; PASS. The patch and hash were regenerated before every round;
the round-1 PASSes cover the site, string and wireframe files, which did not change afterwards.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in `scope_paths`, no stray file. Row links, the collapse predicate, the
  six labels and the gate's check 5 each trace to a #128 ruling quoted in `decisions_taken`; the
  DE/FI wording is disclosed as the builder's draft put to the CPO in the MR head and left in
  `decisions_reserved`, not asserted settled. Check 5 reuses the gate's own locale dictionaries
  and reads two existing seeds — an existing gate extended, no new file, job or invocation
  path; no recurring cost. #57 (`display_group`) and #69 (country table) untouched — the region
  rendering is pre-existing. `08_browse.md` and `00_overview.md` updated in the same branch.
  Impact map honest (no warehouse or export writer). No credential-shaped content.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 3: every exception `_seed_label_keys()` can raise (`KeyError` missing column, `OSError`
  absent/unreadable file, `UnicodeDecodeError` non-UTF-8 bytes, `csv.Error` malformed CSV) lands
  on the gate's own `FAIL:` line and `return 1`; no seed-read path ends in a traceback; the check
  fails closed (never zero keys). The cp1252 test case would fail against the round-2 narrow
  except. `.ruff-ci.toml` selects `E4/E7/E9/F`, so the `noqa: BLE001` is inert and CI lint's
  pass is not a suppression. Only the gate and its tests changed since round 2.
- Round 2: the fieldnames guard and the direct column index fix the zero-keys pass; `main()`'s
  try/except turns an absent file into the FAIL line; the new test goes red against the
  guard-less reader. Verdict then: FAIL (resolved at round 3) — `except (OSError, KeyError)`
  narrower than the message's claim.
- Round 4: the two docstrings carry no date, reviewer, round or MR reference; the comment-history
  test passes; no functional change.
- Round 1: the `SEED_LABEL_FILES` monkeypatch reaches the reader (module global read at call
  time); `test_copy_gate_fails_on_a_seed_key_no_locale_carries` genuinely reds with check 5
  disabled; `encoding="utf-8", newline=""` correct on Windows; a blank cell skipped is right (the
  seeds' `not_null` dbt tests run in the same MR pipeline); the real-seed floors (≥14, ≥7) match
  the files; the Astro inline script only ever narrows visibility, so the page is correct without
  it. Verdict then: FAIL (resolved at round 2) on the zero-keys pass and the bare traceback.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every field the row renders (`slug`, `entity_type`, `confederation`, `competition_name`,
  `logo_url`, `region_label_i18n_key`, `region_label_en`) traced to `_COMPETITION_INDEX_KEEP` in
  the export (a passthrough of `mart_competition_index`) and matched 1:1 against
  `CompetitionIndexRow`; the committed sample has the same 14-key shape and 48 slugs; no
  derivation added. The row link, radio `value` wiring and the collapse script read against
  `rendered_page_evidence.md` §1–3 (48 anchors, 0 `offsetParent` in the built page, the
  background-tab case showing all 8 groups). `a.comp-row` hover/active/focus mirror `a.brow`;
  the row's spans are `display: block`. The six `compType*` keys present in EN/DE/FI, no em
  dash, DE and FI distinct from EN and consistent with the existing pairs. `08_browse.md` §6/§7
  struck and replaced with the #128 text; `00_overview.md` row 08 updated; `metrics_display.md`
  (LOCKED) absent from the diff. Evidence files substantive, on disk.

## escalations
(none)
