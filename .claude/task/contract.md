# Task contract — onboard 3 men's domestic leagues (#72)

objective: >
  Onboard Belgian Pro League, Süper Lig, and Ekstraklasa per GitLab #72. Path B: registry entry +
  generated dbt vars/seed + i18n labels only — zero SQL file changes (no-new-model rule). Women's
  leagues and Liga MX Femenil evaluated in the same issue are explicitly OUT OF SCOPE for this
  task; see decisions_taken.
refs: GitLab #72

impact_map: >
  Leaf/cosmetic short-form: site/i18n/{en,de,fi}.json `competitions` blocks are a flat
  label lookup (league_code -> display string), consumed by the export/frontend for
  rendering only. Adding 3 new keys (BPL/TSL/EKS) does not change any existing key's
  value, does not add computation, and matches the exact pattern of every prior
  domestic-league onboard's i18n step (VL/LMX/LP/MLS/SPL/ED all added the same 3-file,
  1-key-each diff). `grep -rn "i18n" dbt_project/` returns zero hits — dbt has no
  dependency on this file. No mart/number changes; nothing downstream reads these new
  keys except the label lookup itself, which fails closed (missing key = fallback to
  the code) rather than silently computing anything.

scope_paths:
  - docs/competition_registry.yml
  - dbt_project/dbt_project.yml
  - dbt_project/seeds/competition_registry.csv
  - site/i18n/en.json
  - site/i18n/de.json
  - site/i18n/fi.json
  - .claude/task/escalations.log
  - .claude/active_work.md

decisions_taken: >
  Three CPO decisions made in this conversation (2026-08-16), escalated blinded per §11, recorded
  in full in escalations.log as part of this same commit:

  1. history_seasons: 5 for all three leagues. CPO answer: "1. 5" — matches the pattern used for
     every non-Big-5 domestic league onboarded recently (VL, LMX, LP, MLS, SPL, ED all use 5).

  2. Women's leagues (NWSL, Frauen-Bundesliga, Serie A Women, Liga F, Première Ligue, FA WSL) and
     Liga MX Femenil: CPO ruling "drop the women's league all" — none onboarded in this task, no
     exceptions (NWSL had full coverage but is dropped with the rest of the batch). This followed
     live per-fixture verification (not just the season-level coverage flag, which reads
     misleadingly "full" at the season-metadata level): dense sampling of the most recently
     completed season showed real fixture-stats/player-stats presence of 45-60% for four of the
     five European leagues and 0% (0/30 sampled fixtures) for Liga F. The 2026/27 season has not
     started for any of them (all fixtures NS as of 2026-08-16), so "current season" coverage is
     not yet checkable.

  3. WSL: exists in the provider catalog as "FA WSL", provider_league_id 44, England — the original
     #72 research's "not in the provider catalog" finding was a naming-search miss, not an actual
     absence. Moot for this task since it falls under decision 2 (dropped with the women's batch).

  NEW MECHANISM: none — same registry-entry + sync_dbt_vars.py + i18n pattern used for every prior
  domestic-league onboard (issue #260 wave, VL, LMX, LP, MLS, SPL, ED).
  RECURRING COST: 3 new `ingest_active: true` leagues added to the nightly 04:00 UTC pipeline, full
  fanout (fixtures/standings/lineups/stats/events), 5-season backfill each. In line with the cost
  profile of the other domestic-league onboards in this registry.

decisions_reserved:
  - none: the three CPO-class questions in #72 (history_seasons depth, women's-leagues coverage
    verdict, WSL catalog existence) are all resolved above; nothing about this task's scope is open.

done_when:
  - Three new registry entries (BPL, TSL, EKS) in docs/competition_registry.yml, each with a live
    verified provider_league_id, history_seasons: 5, ingest_active: true, status: active.
  - `python scripts/sync_dbt_vars.py` run; dbt_project.yml and seeds/competition_registry.csv both
    regenerated and committed.
  - i18n labels added for BPL/TSL/EKS in en.json, de.json, fi.json.
  - `python scripts/check_registry_var_sync.py` reports OK.
  - `discover_competition.py --audit <code>` reports OK (no `!!!` collision) for each of the 3.
  - escalations.log carries the #72 blinded-escalation entry with the CPO's actual answers.
  - MR opened against main with cost-gate answers and verified IDs in the description.
  - Post-merge operational follow-up (not gated by this commit, but committed to): once the first
    nightly ingest + build have run for BPL/TSL/EKS, run
    `python scripts/diagnostics/verify_competition_ingest.py --league <code> --strict` for each of
    the three per the onboard-competition skill's documented "Operational follow-up after merge"
    step — the check that catches NULL fixture_id (#297), stale wrong-ID fixture-details rows
    (#296), and teams missing from dim_team, exactly the defect class 3 brand-new provider IDs
    risk on first ingest. Flagged by data-engineer-reviewer round 1; report clean --strict output
    (or triage findings) before treating BPL/TSL/EKS as onboarded-and-healthy.

amendments:
  - 2026-08-16: + .claude/active_work.md — authority: standing rule (working_agreement.md §3);
    content: rebase onto gitlab/main pulls in a real conflict on active_work.md (main's nightly-
    status correction overlaps this branch's MR #50/#73 notes) that needs manual resolution.
