# Review — feat/69-country-name-overrides — 2026-08-16

diff_sha256: 29cff0bb9c6c59e18ecafe63b7fedf02dae714d0a74ea75dca661882b40e379b

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- ⛔ ROUND 1 FAILED, correctly. The whole task rests on four CPO rulings governing a §10 naming
  register, and `.claude/task/escalations.log` carried no entry for them — the only 2026-08-16
  entry belonged to a different branch (#72). §11 requires every escalation to land in the log and
  §2 states why: "a reviewer cannot check whether a claimed ruling exists without it." Fixed by
  appending the entry, not by arguing.
- ROUND 2: the new `escalations.log` block covers all four naming rulings plus the fifth
  (seed shape) with the same quotes and reasoning `contract.md` cites — nothing claimed in the
  contract lacks a matching paragraph in the log, and nothing in the log invents authority beyond
  what the contract claims. The entry names the miss plainly ("THIS ENTRY WAS MISSING AND A
  REVIEWER CAUGHT IT") rather than minimising it.
- No code file changed between rounds — verified against `git diff --staged --stat gitlab/main`.
  Round 1's failure was solely the missing log entry, not a finding against the CSV, schema or test.
- `decisions_reserved` keeps `entity_type`, `label_i18n_key`, confederation and the `dim_country`
  supersession question open rather than deciding them. Confirmed they appear as no column in the
  diff: the CSV header stays `provider_country,country_name,source,note`.
- `NEW MECHANISM: none` / `RECURRING COST: none` hold — seed data plus an existing left join, no
  new object, no schedule change.
- Credential sweep of the whole diff: nothing credential-shaped.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: `base_apif__leagues.sql` is confirmed the seed's only reader and applies
  `coalesce(overrides.country_name, leagues.country)`; `dim_league.sql` passes `league_country`
  through with no correction logic. Matches base-corrects / core-publishes
  (`feedback_entity_corrections_in_base`). `grep -rn "league_country"` over `4_intermediate/` and
  `5_marts/` returns zero, confirming the contract's blast-radius claim.
- Test widening: verified the three added staging columns exist with exactly those names by reading
  the models (`stg_apif__teams.team_country`, `stg_apif__coaches.coach_birth_country`,
  `stg_apif__player_profiles.birth_country`). The assertion itself is unchanged — the population it
  compares against grew to match the seed's declared scope. Broadened, not relaxed; no severity
  downgrade.
- Seed content: scanned all 67 `provider_country` values — no duplicates (satisfies the `unique`
  test), no diacritics in any `country_name` (satisfies `done_when`), and duplicate spellings of the
  same country map to identical canonical targets.
- The `Timor-Leste` claim: `!45`'s text calling it "correctly hyphenated, not to be touched" is
  fully removed, the CSV now maps it to `East Timor`, and the new schema text flags the change
  explicitly rather than leaving a stale claim beside contradicting data.
- The two CPO exception rows each cite their own authority in `source`, distinct from the #69 rule
  the other 65 cite.
- Catalogue governance, competition-agnosticism, consumption layer: none apply — no metric, no
  hardcoded league code, no export or frontend file touched.

## escalations
- question: The canonical display name for every country the provider sends — a §10 naming
  register covering 224 entities across four dims.
  CPO ANSWER: recorded in full in `escalations.log` (2026-08-16, feat/69-country-name-overrides).
  Four rulings: "official form"; "Republic of Ireland, keep the long form"; "modern correct name,
  keep the everyday short form"; "the single source of truth is always english" then "No, Ivory
  Coast and Turkey". Plus a fifth on shape: "we only need a mapping between what the provider gives
  us and what we turn into the single source of truth name".
