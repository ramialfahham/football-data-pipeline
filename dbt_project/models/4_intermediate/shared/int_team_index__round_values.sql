{#
  The Teams page value of each round key: club_points for Top clubs, national_stage for
  national teams. Grain: (round_key).
#}

select
    round_key,
    club_points,
    national_stage
from unnest([
    struct('roundGroupStageMatchday' as round_key, 1 as club_points, 1 as national_stage),
    struct('roundGroupMatchday', 1, 1),
    struct('roundLeaguePhaseMatchday', 1, 1),
    struct('roundLeagueStageMatchday', 1, 1),
    struct('compFactMatchday', 1, 1),
    struct('roundWcGroupMatchday', 1, 1),
    struct('roundOf32', 2, 2),
    struct('roundWcOf32', 2, 2),
    struct('roundKnockoutPlayoffs', 2, 2),
    struct('roundOf16', 2, 3),
    struct('roundQuarterFinals', 3, 4),
    struct('roundQuarterfinalsAm', 3, 4),
    struct('roundSemiFinals', 4, 5),
    struct('roundSemifinalsAm', 4, 5),
    struct('roundFinal', 5, 6),
    struct('roundQualifyingRound1', 0, null),
    struct('roundQualifyingRound2', 0, null),
    struct('roundQualifyingRound3', 0, null),
    struct('roundPlayoffRound', 0, null),
    struct('roundAfcPreliminaryStage', 0, null),
    struct('roundPreliminaryRound', 0, null),
    struct('roundPreliminaryRound1', 0, null),
    struct('roundPreliminaryRound2', 0, null),
    struct('roundLiberStage1', 0, null),
    struct('roundLiberStage2', 0, null),
    struct('roundLiberStage3', 0, null)
])
