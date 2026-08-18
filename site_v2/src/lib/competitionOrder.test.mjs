// Pins the CPO-approved ordering rule (escalations.log, 2026-08-16) against the exact failure
// modes it was written to prevent: a raw-clock tiebreak beating the calendar-day bucket, and a
// no-upcoming competition outranking one that has a fixture coming up.

import { test } from "node:test";
import assert from "node:assert/strict";
import { compareCompetitions, groupAndOrderCompetitions } from "./competitionOrder.mjs";

function row(overrides) {
  return {
    league_code: "ZZ",
    competition_type: "domestic_league",
    entity_type: "club",
    slug: "zz",
    category_label_en: "Domestic leagues",
    category_label_i18n_key: "compTypeDomesticLeague",
    confederation: "UEFA",
    region_rank: 1,
    competition_name: "ZZ",
    logo_url: null,
    next_kickoff_datetime: null,
    last_kickoff_datetime: null,
    region_label_en: "Zed",
    region_label_i18n_key: null,
    ...overrides,
  };
}

test("an upcoming fixture always outranks no fixture, regardless of region_rank", () => {
  const upcoming = row({ league_code: "OFC1", region_rank: 7, next_kickoff_datetime: "2026-09-01 10:00:00+00:00" });
  const dormant = row({ league_code: "UEFA1", region_rank: 1, next_kickoff_datetime: null, last_kickoff_datetime: "2026-08-30 19:00:00+00:00" });
  assert.equal(compareCompetitions(upcoming, dormant), -1);
  assert.equal(compareCompetitions(dormant, upcoming), 1);
});

test("calendar-day bucket beats raw kickoff time — a later day never jumps an earlier day", () => {
  // Day 1, 23:00, region_rank 7 (worst) vs Day 2, 01:00, region_rank 1 (best). If this compared
  // raw timestamps, the region_rank-1 row's earlier clock time would still lose to the actual
  // earlier day — this asserts day always wins regardless of what time-of-day or region_rank say.
  const day1Late = row({ league_code: "A", region_rank: 7, next_kickoff_datetime: "2026-08-20 23:00:00+00:00" });
  const day2Early = row({ league_code: "B", region_rank: 1, next_kickoff_datetime: "2026-08-21 01:00:00+00:00" });
  assert.equal(compareCompetitions(day1Late, day2Early), -1, "day 1 must sort before day 2 even with a worse region_rank and a later clock time");
});

test("same calendar day ties break on region_rank, not on clock time", () => {
  const earlyClockWorseRegion = row({ league_code: "A", region_rank: 5, next_kickoff_datetime: "2026-08-20 10:00:00+00:00" });
  const lateClockBetterRegion = row({ league_code: "B", region_rank: 1, next_kickoff_datetime: "2026-08-20 22:00:00+00:00" });
  assert.ok(
    compareCompetitions(lateClockBetterRegion, earlyClockWorseRegion) < 0,
    "the 22:00 kickoff must sort first because its region_rank is better, despite the later clock time",
  );
});

test("same day and same region_rank breaks the tie by kickoff time, then by league_code", () => {
  const earlier = row({ league_code: "Z", region_rank: 1, next_kickoff_datetime: "2026-08-20 10:00:00+00:00" });
  const later = row({ league_code: "A", region_rank: 1, next_kickoff_datetime: "2026-08-20 18:00:00+00:00" });
  assert.equal(compareCompetitions(earlier, later), -1, "kickoff time is the tiebreak before league_code, even though A < Z alphabetically");
});

test("no-upcoming rows sort most-recently-played first, never-played sorts last of all", () => {
  const recentlyPlayed = row({ league_code: "A", last_kickoff_datetime: "2026-08-10 19:00:00+00:00" });
  const longAgo = row({ league_code: "B", last_kickoff_datetime: "2024-01-01 19:00:00+00:00" });
  const neverPlayed = row({ league_code: "C", last_kickoff_datetime: null });
  assert.equal(compareCompetitions(recentlyPlayed, longAgo), -1);
  assert.equal(compareCompetitions(longAgo, neverPlayed), -1);
  assert.equal(compareCompetitions(neverPlayed, recentlyPlayed), 1);
});

test("groupAndOrderCompetitions orders categories by their own earliest-sorting member", () => {
  // "qualifying" category's only member kicks off TODAY; "domestic_league" category's only
  // member kicks off next week. The 2026-08-16 note's own example: national teams rank ahead of
  // club leagues during a break, with no special case beyond applying the same key one level up.
  const qualifier = row({
    league_code: "WCQ", competition_type: "qualifying",
    category_label_en: "National team qualifiers", category_label_i18n_key: "compTypeQualifying",
    next_kickoff_datetime: "2026-08-20 18:45:00+00:00",
  });
  const league = row({
    league_code: "PL", competition_type: "domestic_league",
    category_label_en: "Domestic leagues", category_label_i18n_key: "compTypeDomesticLeague",
    next_kickoff_datetime: "2026-08-27 19:00:00+00:00",
  });
  const categories = groupAndOrderCompetitions([league, qualifier]);
  assert.deepEqual(categories.map((c) => c.key), ["qualifying", "domestic_league"]);
});

test("groupAndOrderCompetitions sorts rows within each category too", () => {
  const later = row({ league_code: "B", competition_type: "domestic_league", next_kickoff_datetime: "2026-08-25 19:00:00+00:00" });
  const earlier = row({ league_code: "A", competition_type: "domestic_league", next_kickoff_datetime: "2026-08-20 19:00:00+00:00" });
  const categories = groupAndOrderCompetitions([later, earlier]);
  assert.equal(categories.length, 1);
  assert.deepEqual(categories[0].rows.map((r) => r.league_code), ["A", "B"]);
});
