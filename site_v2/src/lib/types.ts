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
