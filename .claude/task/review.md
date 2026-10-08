# Review — feature/166-match-page-marts

diff_sha256: 94edc88c32102f929d018623953466ec1dcd7d2837ad0d2d44e0fbf617dbef3f

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every non-task file in the diff is in scope_paths; no amendment lacks authority.
- The §10 items (warehouse-first split, no new model, the §1/§4 window rules, the §1 enforcement test) are recorded in decisions_taken; nothing in decisions_reserved is touched.
- scorer_points_player is an existing catalogue metric generated onto int_player_season_record, so no invented metric; no frontend file is touched.
- The impact map's reader claims hold: int_player_profile__yoy names its columns, and dbt ls shows no downstream model of either mart.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round-1 findings resolved: int_player_club_season__metrics is untouched; metrics_context_model.md and the window_type__season_record block are untouched and true; recent_meetings.home_away uses doc('home_away'); top_player_rank is NULL when goals plus assists is unknown.
- The generated scorer_points_player matches the catalogue formula and the Surface order; the mart only selects and ranks; minutes_to_date applies the same completeness gate.
- The side-level window choice keeps the (upcoming_fixture_sk, team_sk, player_sk) grain unique and follows the §4 fallback.
- assert_season_record_within_one_competition reads columns both season-record marts carry; the formula recompute test already covers scorer_points_player on int_player_season_record.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The generator change adds one metric to the int_player_season_record surface; the generated block's position and layout match; the drift test in test:python stays the arbiter.
- Round-1 findings closed: the rank-order test fails on a flipped sort, a dropped key or a minutes order change; the mirror branch catches a missing mirror, a duplicated side and a wrong side taken in the mart.
- The within-one-competition test's player bound counts every leg, so it never false-fails; the rank partition keeps non-null ranks contiguous.
- No hook, workflow, CI, dependency, credential or site change.

## escalations
(none)
