// Types for the team payload (scripts/export_site_data.py :: shape_team_payload,
// over mart_team_profile). The frontend reads these; it never reshapes facts.
// Metric-rate fields (goals_per_match, …) are read positionally via metricRows.ts
// and accessed with a Record cast + asNumber — same pattern as the fixture WindowStats.

export interface TeamFixture {
  opponent_name?: string | null;
  opponent_logo_url?: string | null;
  is_home?: boolean | null;
  kickoff_datetime?: string | null;
  round_name?: string | null;
  goals_for?: number | null;
  goals_against?: number | null;
  result?: string | null;
  status_short?: string | null;
}

export interface Venue {
  name?: string | null;
  city?: string | null;
  capacity?: number | null;
}

/** One `seasons[]` row: a mart_team_profile row (identity stripped) + fixtures. */
export interface TeamSeason {
  league_code: string;
  season_api_year: number;
  competition_type?: string | null;
  // record / rank / form (mart_team_season)
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
  // season-metric coverage (captions)
  season_games_played?: number | null;
  stat_coverage_season_games?: number | null;
  player_stat_coverage_season_games?: number | null;
  // year-over-year (domestic only; null otherwise)
  yoy_games_played_cutoff?: number | null;
  points_this_season?: number | null;
  points_prev_season?: number | null;
  points_delta_yoy?: number | null;
  goals_for_this_season?: number | null;
  goals_for_prev_season?: number | null;
  goals_for_delta_yoy?: number | null;
  goals_against_this_season?: number | null;
  goals_against_prev_season?: number | null;
  goals_against_delta_yoy?: number | null;
  // streaks (trailing runs as of the latest match)
  unbeaten_run?: number | null;
  win_run?: number | null;
  winless_run?: number | null;
  clean_sheet_run?: number | null;
  scoring_run?: number | null;
  // fixtures (GAP-15): next fixture + last-5 results
  next_fixture?: TeamFixture | null;
  recent_results?: TeamFixture[];
  // metric-rate fields (goals_per_match … save_ratio) live here too — read via cast.
}

export interface TeamPayload {
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

/**
 * The season shown by default: the most-recent domestic league (seasons[] is served
 * sorted year desc), else the most-recent season. SELECTION of a served row — not a
 * derivation. The multi-season selector swap is deferred (island, #362).
 */
export function pickDefaultSeason(seasons: TeamSeason[]): TeamSeason | undefined {
  return seasons.find((s) => s.competition_type === "domestic_league") ?? seasons[0];
}
