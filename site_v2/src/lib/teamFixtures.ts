// A team's served schedule in the shapes the site's shared rows take: an upcoming match as THE
// match row's fixture (home and away from the served `is_home`), a result as the result row's
// match. The competition's name, address and crest come from the registry's exported copies.
import competitions from "../data/competitions.json";
import competitionIndex from "../data/competition_index.json";
import { builtFixtures } from "./builtFixtures.mjs";
import type { CompetitionFixture, FormMatch, TeamScheduleFixture, TeamRef } from "./types";

export interface CompetitionInfo {
  code: string;
  name: string;
  slug: string | null;
  crest: string | null;
}

const NAMES = competitions as Record<string, { slug?: string; name?: string }>;
const INDEX = new Map(
  (competitionIndex as { competitions: { league_code: string; competition_name?: string; slug?: string; logo_url?: string }[] })
    .competitions.map((c) => [c.league_code, c]),
);

export function competitionInfo(code: string): CompetitionInfo {
  const row = INDEX.get(code);
  return {
    code,
    name: row?.competition_name ?? NAMES[code]?.name ?? code,
    // only a competition of the index has a page
    slug: row?.slug ?? null,
    crest: row?.logo_url ?? null,
  };
}

export function asMatchRowFixture(fx: TeamScheduleFixture, team: TeamRef): CompetitionFixture {
  const opponent: TeamRef = { team_id: null, name: fx.opponent_name ?? "", slug: null, crest: fx.opponent_logo_url ?? null };
  return {
    fixture_id: fx.fixture_id,
    slug: builtFixtures().get(fx.fixture_id)?.slug ?? null,
    kickoff: fx.kickoff_datetime ?? null,
    status: fx.status_short ?? null,
    is_played: false,
    goals_home: null,
    goals_away: null,
    home: fx.is_home ? team : opponent,
    away: fx.is_home ? opponent : team,
    is_match_that_matters: false,
  };
}

export function asResultMatch(fx: TeamScheduleFixture, recency: number): FormMatch {
  return {
    recency_rank: recency,
    played_fixture_sk: fx.fixture_id,
    played_league_code: fx.league_code,
    played_kickoff_datetime: fx.kickoff_datetime,
    played_round_name: fx.round_name,
    home_away: fx.is_home == null ? null : fx.is_home ? "home" : "away",
    goals_for: fx.goals_for,
    goals_against: fx.goals_against,
    result: fx.result,
    opponent_name: fx.opponent_name,
    opponent_logo_url: fx.opponent_logo_url,
  };
}

/** Upcoming matches grouped by competition, each group's matches soonest first and the groups in
 *  the order of their first match (Home's rule). */
export function upcomingByCompetition(upcoming: TeamScheduleFixture[]): { code: string; fixtures: TeamScheduleFixture[] }[] {
  const groups = new Map<string, TeamScheduleFixture[]>();
  for (const fx of upcoming) {
    if (!groups.has(fx.league_code)) groups.set(fx.league_code, []);
    groups.get(fx.league_code)!.push(fx);
  }
  return [...groups].map(([code, fixtures]) => ({ code, fixtures }));
}
