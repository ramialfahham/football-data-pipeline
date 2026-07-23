// Types for the fixture payload (scripts/export_site_data.py :: shape_fixture_payload).
// Mirrors the served shape; the frontend reads these, never reshapes facts.

export interface WindowStats {
  window_type?: string | null;
  games_in_window?: number | null;   // W1
  games_played?: number | null;      // W2
  games_with_team_stats?: number | null;
  contributing_competitions?: string[] | null;
  points_won?: number | null;
  wins?: number | null;              // W2
  draws?: number | null;             // W2
  losses?: number | null;            // W2
  season_api_year?: number | null;
  // metric fields (goals_per_match, pass_accuracy, clean_sheets, games, …)
  [key: string]: number | string | string[] | null | undefined;
}

export interface Standing {
  group_name?: string | null;
  is_knockout?: boolean | null;
  league_rank?: number | null;
  standing_points?: number | null;
  standing_played?: number | null;
  standing_goals_diff?: number | null;
  standing_form?: string | null;
}

export interface FormMatch {
  recency_rank: number;
  played_fixture_sk?: number | null;
  played_league_code?: string | null;
  played_kickoff_datetime?: string | null;
  played_round_name?: string | null;
  home_away?: string | null;
  goals_for?: number | null;
  goals_against?: number | null;
  result?: string | null;
  opponent_name?: string | null;
  opponent_logo_url?: string | null;
  has_team_stats?: boolean | null;
  has_player_stats?: boolean | null;
}

export interface TopPlayer {
  player_sk: number;
  position_code?: string | null;
  goals_total?: number | null;
  goals_assists?: number | null;
  saves?: number | null;
  save_pct?: number | null;
  shots_on?: number | null;
  passes_key?: number | null;
  player_name?: string | null;
  player_photo_url?: string | null;
}

export interface Side {
  team_id: number;
  name?: string | null;
  crest?: string | null;
  country?: string | null;
  w1?: WindowStats | null;
  w2?: WindowStats | null;
  standing?: Standing | null;
  form_window?: FormMatch[];
  top_players?: TopPlayer[];
}

export interface RecentMeeting {
  kickoff_datetime?: string | null;
  league_code?: string | null;
  goals_for?: number | null;
  goals_against?: number | null;
  result?: string | null;
}

export interface HeadToHead {
  total_meetings?: number | null;
  wins?: number | null;
  draws?: number | null;
  losses?: number | null;
  goals_for?: number | null;
  goals_against?: number | null;
  meetings_last5?: number | null;
  last_meeting_at?: string | null;
  last_meeting_league_code?: string | null;
  last_meeting_goals_for?: number | null;
  last_meeting_goals_against?: number | null;
  last_meeting_result?: string | null;
  recent_meetings?: RecentMeeting[];
}

export interface Fixture {
  type: string;
  fixture_id: number;
  slug: string;
  kickoff?: string | null;
  status?: string | null;
  league_code: string;
  league_name?: string | null;
  season?: number | null;
  round?: string | null;
  venue?: string | null;
  home: Side;
  away: Side;
  head_to_head?: HeadToHead | null;
}

/** Narrow a payload value to a finite number (metric fields arrive as number | null). */
export function asNumber(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

// ---------------------------------------------------------------------------
// Team payload (scripts/export_site_data.py :: shape_team_payload, over
// mart_team_profile + mart_team_fixtures). Mirrors the served shape; the frontend
// reads these and never reshapes facts.
// ---------------------------------------------------------------------------

export interface Venue {
  name?: string | null;
  city?: string | null;
  capacity?: number | null;
}

export interface TeamFixture {
  opponent_name?: string | null;
  opponent_logo_url?: string | null;
  is_home?: boolean | null;
  kickoff_datetime?: string | null;
  round_name?: string | null;
  goals_for?: number | null;
  goals_against?: number | null;
  result?: string | null;      // "W" | "D" | "L" | null (upcoming)
  status_short?: string | null;
}

/** One team in the league-season deserved-vs-actual scatter (the hero). Every value is
 *  a served column the model already computed; `deserved` is its least-squares fit. */
export interface ScatterDot {
  sotd: number | null;          // shots-on-target difference per match (x)
  points: number | null;        // points won (y)
  deserved: number | null;      // the model's deserved_points at this team (on the trend line)
  is_self: boolean;
}

/** One rank-vs-league benchmark row (mart_team_competition_benchmarks) — the Performance
 *  tab's "vs the league" panel. `rank` is RAW value-descending (the frontend makes it
 *  direction-aware for display); `metric_value`/`league_median` are the served units
 *  (ratios 0..1 for percent metrics; clean_sheets is served as a rate, not a count). */
export interface Benchmark {
  metric_key: string;
  metric_value?: number | null;
  rank?: number | null;
  team_count?: number | null;
  league_median?: number | null;
  league_p25?: number | null;
  league_p75?: number | null;
  vs_median_delta?: number | null;
}

/** One `seasons[]` row: a mart_team_profile row (identity stripped) + fixtures + scatter. */
export interface TeamSeason {
  league_code: string;
  season_api_year: number;
  competition_type?: string | null;
  // record / rank / form
  latest_rank?: number | null;
  points?: number | null;
  played?: number | null;
  wins?: number | null;
  draws?: number | null;
  losses?: number | null;
  goals_for?: number | null;
  goals_against?: number | null;
  goal_diff?: number | null;
  clean_sheets?: number | null;
  latest_form?: string | null;
  season_games_played?: number | null;
  // deserved-vs-actual (domestic single-ladder only; null otherwise)
  deserved_points?: number | null;
  sot_points_gap?: number | null;
  sot_difference_per_match?: number | null;
  shots_on_goal_per_match?: number | null;
  shots_on_goal_against_per_match?: number | null;
  deserved_scatter?: ScatterDot[];
  // year-over-year (games-aligned; domestic only, null otherwise)
  yoy_games_played_cutoff?: number | null;
  points_this_season?: number | null;
  points_delta_yoy?: number | null;
  goals_for_this_season?: number | null;
  goals_for_delta_yoy?: number | null;
  goals_against_this_season?: number | null;
  goals_against_delta_yoy?: number | null;
  // fixtures (GAP-15): next fixture + last-5 results
  next_fixture?: TeamFixture | null;
  recent_results?: TeamFixture[];
  // rank-vs-league benchmarks (GAP-23) — the Performance tab's "vs the league" panel.
  benchmarks?: Benchmark[];
  // the 16 metric values + their `{field}_delta_yoy` also live on this row and are read
  // positionally via a Record cast (same pattern as the fixture WindowStats).
}

export interface Team {
  type: string;
  team_id: number;
  slug: string;
  name?: string | null;
  country?: string | null;
  crest?: string | null;
  founded_year?: number | null;
  venue?: Venue | null;
  seasons: TeamSeason[];
}
