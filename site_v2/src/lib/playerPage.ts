// What the Player page reads: the payload's shape, the served metric rows in their groups, and the
// words a position takes in a sentence. Selection and wording only; every value is served.
import { existsSync } from "node:fs";
import { join } from "node:path";
import metricGroups from "../data/metric_groups.json";
import playerMetricRows from "../data/player_metric_rows.json";
import { t } from "../i18n/strings";
import type { Lang } from "./format";
import type { FormMatch, TeamRef, TeamScheduleFixture } from "./types";

export interface PlayerMetric {
  metric_key: string;
  value: number | null;
  rank: number | null;
  median: number | null;
  others?: number[];
}
export interface PlayerCompetition {
  league_code: string;
  season: number;
  season_label: string | null;
  position_group: string;
  player_count: number | null;
  metrics: PlayerMetric[];
}
export interface PlayerSquad {
  team: TeamRef;
  player_count: number | null;
  metrics: PlayerMetric[];
}
export interface PlayerLastSeason {
  minutes: number | null;
  minutes_prev: number | null;
  metrics: { metric_key: string; value: number | null; value_prev: number | null }[];
}
export interface PlayerMatch extends FormMatch {
  minutes: number | null;
  goals: number | null;
  assists: number | null;
  ball_actions: number | null;
  on_bench: boolean;
}
export interface PlayerTab {
  tab: "club" | "national_team";
  team: TeamRef | null;
  cards: Record<string, number | null>;
  next_matches: TeamScheduleFixture[];
  competitions: PlayerCompetition[];
  squad: PlayerSquad | null;
  last_season: PlayerLastSeason | null;
  recent_matches: PlayerMatch[];
}
export interface Player {
  player_id: number;
  slug: string;
  name: string | null;
  photo: string | null;
  nationality: string | null;
  age: number | null;
  height: string | null;
  position_group: string | null;
  season_label: string | null;
  club: TeamRef | null;
  shares_name_at_club?: boolean;
  tabs: PlayerTab[];
}

export interface PlayerMetricRow {
  metric_id: string;
  label_i18n_key: string;
  metric_group: string;
  metric_order: number;
  direction: string;
  format: "decimal_1" | "decimal_0" | "percent" | "integer";
  is_key_metric: boolean;
}
export interface PlayerMetricGroup {
  key: string;
  rows: PlayerMetricRow[];
  hasKey: boolean;
}

/** The served rows among `has`, under the catalogue's groups in their order; a goalkeeper's own
 *  group opens the list. */
export function playerGroups(has: (metricId: string) => boolean, isGoalkeeper = false): PlayerMetricGroup[] {
  const served = playerMetricRows.rows as PlayerMetricRow[];
  return [...metricGroups.groups]
    .sort((a, b) => Number(isGoalkeeper && b.key === "goalkeeping") - Number(isGoalkeeper && a.key === "goalkeeping") || a.order - b.order)
    .map((g) => {
      const rows = served
        .filter((r) => r.metric_group === g.key && has(r.metric_id))
        .sort((a, b) => a.metric_order - b.metric_order);
      return { key: g.key, rows, hasKey: rows.some((r) => r.is_key_metric) };
    })
    .filter((g) => g.rows.length > 0);
}

/** Whether this build makes the team's page: the route emits one per file in src/data/teams. */
export function teamHasPage(teamId: number | null | undefined): boolean {
  return teamId != null && existsSync(join(process.cwd(), "src/data/teams", `${teamId}.json`));
}

/** A position in a sentence: `One` a person, `Peers` the explainer's form, `Others` the legend's. */
export function positionWord(lang: Lang, form: "One" | "Peers" | "Others", group: string | null | undefined): string {
  return group ? t(lang, `playerPos${form}${group}`) : "";
}

/** The team before Finnish "-pelaajaan": joined to a one-word name, set apart after several words. */
export function teamBeforeCompound(lang: Lang, team: string): string {
  if (lang !== "fi") return team;
  return team.includes(" ") ? `${team} -` : `${team}-`;
}

/** Where a metric's value sits on its line, inside the inset at each end so no dot is cut. */
export function placeOnLine(v: number, lo: number, hi: number, inset: number): number {
  return hi === lo ? 50 : inset + ((v - lo) / (hi - lo)) * (100 - 2 * inset);
}

/** How a median's value stands on its tick: centred, and held inside the line at each end. */
export function medianAnchor(left: number): "start" | "middle" | "end" {
  const edge = 8;
  return left < edge ? "start" : left > 100 - edge ? "end" : "middle";
}
