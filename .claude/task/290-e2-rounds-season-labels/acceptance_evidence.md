# Verification — two rounds under one name, and season labels by edition

Read on this branch through the site's own round-name path: `roundName` (`site_v2/src/lib/roundName.mjs`, the function MatchdaySchedule.astro and TeamCompetitions.astro call) with `t` from `site_v2/src/i18n/strings.ts`, run under node 24 for each key and language. The keys are the ones `int_round_names` serves for the corrected fixtures: the new UCL `round_names` rows 88 and 89, and the existing CAFCL rows 91 and 92. On prod, the corrections applied to `fct_fixture` resolve all 44 fixtures and leave 0 teams with two ties in one round (3.9 MB query).

criteria_demonstrated:
  - **Semi-finals key:** `roundPreliminarySemiFinals` renders "Preliminary round · Semi-finals" (en), "Vorrunde, Halbfinale" (de), "Esikarsinta, välierät" (fi).
  - **Final key:** `roundPreliminaryFinal` renders "Preliminary round · Final" (en), "Vorrunde, Finale" (de), "Esikarsinta, finaali" (fi).
  - **Every served key has a string in all three languages:** the UCL 2019, 2021, 2022 and 2023 preliminary fixtures resolve to `roundPreliminarySemiFinals` and `roundPreliminaryFinal` (above); the CAF Champions League 2025 preliminary fixtures resolve to `roundPreliminaryRound1` ("First preliminary round", "1. Qualifikationsrunde", "1. karsintakierros") and `roundPreliminaryRound2` ("Second preliminary round", "2. Qualifikationsrunde", "2. karsintakierros"). No key renders as its own name or as empty in any language.
