// Fixture-page chrome strings (DE / EN / FI). The ~two dozen UI labels the fixture
// template needs. Metric ROW labels are the locked display strings in
// lib/metricRows.ts (identical across locales for now); wiring per-locale metric
// labels from the catalogue i18n keys is a follow-up (#370). Fresh to site_v2 — the
// MVP's site/i18n/ is a separate surface. Translations are standard football-UI terms;
// native DE/FI review welcome (noted in the handover).

import type { Lang } from "../lib/format";

type Dict = Record<string, string>;

/** The product name, in ONE place. Interpolated into strings via `t()`'s `{brand}` param.
 *
 * Deliberately a plain constant substituted at call time rather than a template literal inside
 * the dictionaries: `site_v2/scripts/check-page-specs.mjs` extracts the EN key set with
 * `/([A-Za-z0-9_-]+):\s*"/g`, which matches on a DOUBLE QUOTE. Rewriting a dictionary entry as
 * a backtick template would silently drop that key from the set the build gate checks, and the
 * gate's own `MIN_EXPECTED_KEYS` floor is too coarse to notice two keys going missing. Keep every
 * dictionary value double-quoted. */
export const BRAND = "Matchday Pilot";

const EN: Dict = {
  crumbHome: "Home",
  crumbMatches: "Matches",
  eyebrowPreview: "Match preview",
  secForm: "Form comparison",
  secRecent: "Recent matches",
  secPlayers: "Players to watch",
  secH2H: "Head to head",
  secAbout: "About this match",
  secExplore: "Explore",
  segLast5: "Last 5",
  segSeason: "This season",
  scopeAllComps: "all competitions",
  vs: "vs",
  pts: "pts",
  goals: "goals",
  assists: "assists",
  saves: "saves",
  incl: "incl.",
  throughMatchday: "through matchday {n}",
  lastSeason: "last season ({year})",
  playersWindow: "Last 5 matches",
  statsCoverage: "stats from {a} of {b} matches",
  meetings: "meetings",
  draws: "draws",
  goalsWord: "goals",
  lastMeeting: "Last",
  firstMeeting: "First-ever meeting",
  h2hLastDrawn: "The last meeting was drawn.",
  h2hLastWon: "{club} won the last meeting.",
  h2hBothDrawn: "Both of the last 2 meetings were drawn.",
  h2hAllDrawn: "All of the last {n} meetings were drawn.",
  h2hWonBoth: "{club} won both of the last 2 meetings.",
  h2hWonAll: "{club} won all of the last {n} meetings.",
  h2hWonSomeOneDrawn: "{club} won {won} of the last {n} meetings, and 1 was drawn.",
  h2hWonSomeDrawn: "{club} won {won} of the last {n} meetings, and {d} were drawn.",
  h2hSplit: "{home} won {w} and {away} {l} of the last {n} meetings.",
  h2hSplitOneDrawn: "{home} won {w} and {away} {l} of the last {n} meetings, and 1 was drawn.",
  h2hSplitDrawn: "{home} won {w} and {away} {l} of the last {n} meetings, and {d} were drawn.",
  h2hNone: "No meetings on record.",
  formIntro: "Form metrics from each team's last 5 matches across all competitions.",
  formIntroPrev: "Form metrics from each team's last 5 matches across all competitions; before a team's first {competition} match, from its last {competition} season.",
  playersIntro: "Each team's leading players {in} this season, by goals plus assists.",
  playersIntroPrev: "Each team's leading players {in} by goals plus assists; before a team's first match in it, last season's.",
  compIn: "in {competition}",
  compInMasculine: "in {competition}",
  haHome: "H",
  haAway: "A",
  noRecentForm: "No recent matches",
  noMatchStats: "match stats not available",
  timeTBD: "time TBD",
  table: "Table",
  fullH2H: "Full head-to-head",
  footnote: "Sample data · v2 preview ({brand})",
  aboutWithH2h: "{home} vs {away} · {round}. The two clubs have met {meetings} times: {record}.",
  aboutNoH2h: "{home} vs {away} · {round}.",
  posF: "Forward", posM: "Midfield", posD: "Defence", posG: "Goalkeeper",
  // --- team page (Overview) ---
  crumbTeams: "Teams",
  crumbAria: "Breadcrumb",
  tabsAria: "Team sections",
  founded: "Founded",
  tabOverview: "Overview",
  tabPerformance: "Performance",
  tabSquad: "Squad",
  teamPerfIntro: "{competition} {season}: {team} compared with the other teams and with the season before. Other competitions are not included.",
  teamLeaguePhase: "League phase",
  teamThrough: "Through",
  teamKnockedOut: "Knocked out",
  teamWinners: "Winners",
  teamHighsLows: "Highs and lows",
  teamBiggestWin: "Biggest win",
  teamHeaviestDefeat: "Heaviest defeat",
  teamVsHome: "vs {opponent}",
  teamAtAway: "at {opponent}",
  teamUpcoming: "Upcoming",
  teamResults: "Results",
  teamStanding: "Standing",
  teamPosition: "Position",
  teamSeasonBefore: "Season before: {value}",
  teamAfterMatches: "{competition}, after {n} matches",
  teamOtherTeams: "Other {competition} teams",
  teamScatterAria: "{pointsName} and {sotdName} per match of every {competition} team, with the {deservedName} line.",
  teamVsLeague: "Compared with the league",
  teamVsLeagueIntro: "Each value is ranked against the other {competition} clubs this season. The median splits the league in two: half the clubs are above it, half below.",
  teamLeagueMedian: "League median",
  teamBetterLeft: "← better",
  teamBetterRight: "better →",
  teamVsLastSeason: "Compared with last season",
  teamVsLastSeasonIntro: "Both seasons are compared over their first {n} matches.",
  teamThisSeasonHead: "This season",
  teamLastSeasonHead: "Last season",
  teamTrend: "Trend",
  teamTrendBetter: "better than last season",
  teamTrendWorse: "worse than last season",
  teamTrendSame: "same as last season",
  appearanceCountOne: "{n} appearance",
  appearanceCount: "{n} appearances",
  filterAllCompetitions: "All competitions",
  filterByCompetition: "Filter by competition",
  comingTitle: "Coming soon",
  comingPerformance: "Every metric ranked against the league and against last season. Landing with the next release.",
  comingSquad: "The full squad with per-player minutes and output. Landing with the next release.",
  // squad tab
  squadGk: "Goalkeepers", squadDef: "Defenders", squadMid: "Midfielders", squadFwd: "Forwards", squadOther: "Other",
  seasonToDate: "season to date",
  goalOne: "goal", assistOne: "assist",
  median: "Median",
  secDeserved: "Deserved vs actual",

  // SEO templates (#844). These are the ONLY reason a page's <title> and <meta description> differ
  // across locales: the entity name and the competition name are locale-independent (the registry
  // carries one `name` per competition), so the DESCRIPTIVE words carry the whole locale signal.
  // Before this, all three locales shipped byte-identical titles and descriptions.
  // Shape follows the approved wireframes verbatim -- 02_team_profile.md section 8 ends the team
  // title with the brand; 01_fixture_page.md section 8 ends the fixture title with the competition.
  // NO NUMBERS in these until #838 lands: `points` is a synthetic 3-1-0 tally computed regardless of
  // the competition's rules, so a templated "N points" would write a known-false figure into a
  // surface search engines cache independently of the page.
  // Colon, not an em dash: the dash reads as AI-generated, and it is a tell,
  // especially as a clause separator. A colon is the conventional
  // entity-then-descriptor form in a page title, reads as edited rather than generated, and costs
  // two characters less against a budget these titles already overrun.
  // The middle is deliberately SHORT. It is byte-identical on all 3,250 team pages, so it
  // differentiates nothing between them, while the two parts that DO vary (the brand here, the
  // competition on the fixture title) are exactly what Google truncates first. Measured: the long
  // middle put the team title at 64 characters for "Manchester United" and 71 for "Borussia
  // Mönchengladbach", pushing the brand out of the result entirely. Spending the budget on a
  // constant and losing the variable is the wrong way round.
  // NO brand suffix — a reversal of an earlier "keep the brand" rule: a suffix is EARNED by
  // equity, not a way to build it. It cost 17
  // characters — 28-36% of the title budget — on ~9,750 team page/locale combinations, and with
  // 3,250 identical suffixes Google reads it as boilerplate and truncates it anyway. The brand does
  // NOT leave the page: Layout.astro emits `og:site_name` unconditionally. Reinstate when branded
  // query volume in Search Console shows the name has something to trade on.
  // Four descriptors, not two. It was cut to "Stats & Form" to make room for the brand suffix, and
  // once the suffix went the cut had no reason left — 31 characters against a ~600px budget wasted
  // half the title. Each word maps to a query the page ANSWERS: Stats -> Performance benchmarks,
  // Form -> the Overview form window, Squad -> the Squad tab, Fixtures -> the fixtures block.
  // Nothing here is promised that the page does not render. Measured worst case (Borussia
  // Mönchengladbach): 516px EN / 543px DE / 554px FI, all inside 600px.
  seoTeamTitle: "{team}: Stats, Form, Squad & Fixtures",
  // Parentheses, same as DE and FI. "in {competition}" has the IDENTICAL defect English-side that
  // it had in German: "in THE Premier League" and "in THE Championship" take an article, "in Serie
  // A" and "in Ligue 1" do not, and a template cannot know which it has. I fixed German for exactly
  // this reason and left English alone — treating it as the trusted baseline, which is its own
  // failure class.
  seoTeamDesc: "{team} ({competition}): form, fixtures, squad and season statistics.",
  // NO descriptive middle on the fixture title. It carries TWO entity names plus a competition, so
  // any middle at all overruns: with "Form & Stats" the German came to 69 and the Finnish to 65.
  // Nothing is really lost — the query for a fixture page IS the two team names, "vs" already says
  // what kind of page this is, and the competition is the part that distinguishes a league meeting
  // from a cup tie. The keyword was costing the differentiator.
  // Shape matches seoTeamTitle above — `{entity}: <descriptor>`, no brand suffix — for the SAME
  // reason recorded there: a suffix is earned by equity, and an identical one on every page
  // reads as boilerplate.
  //
  // The competition is NOT in the title, and that is researched rather than preferred. Sofascore
  // ("SJK vs HJK live score, H2H and lineups | Sofascore") and FBref ("... Match Report - <date> |
  // FBref.com") both omit it; kicker uses an editorial headline with the teams only in the URL.
  // Keeping it failed 4 of 26 competitions against the 660px hard cap, worst 886px. It is not
  // lost: it stays in the breadcrumb, the URL and the JSON-LD superEvent.
  // The date (short day and month, UTC) tells apart two meetings of the same clubs, which would
  // otherwise share a title; with no descriptor word the title stays true once a match is played.
  // Measured over every real upcoming fixture: worst 535px, inside the 600px budget.
  seoFixtureTitle: "{home} vs {away}, {date}",
  // --- chrome (site-wide header/footer, #825) ---
  navCompetitions: "Competitions",
  navMatches: "Matches",
  navTeams: "Teams",
  navPlayers: "Players",
  navStandings: "Standings",
  navStatistics: "Statistics",
  mainNavAria: "Main navigation",
  searchPlaceholder: "Search teams, players…",
  searchAria: "Search",
  themeToggleAria: "Toggle theme",
  menuAria: "Menu",
  footerAbout: "About",
  footerImprintPending: "Imprint (pending)",
  footerDataSource: "Data: API-Football",
  // --- landing (#367). PLACEHOLDER COPY: every string below is the product owner's (§10) and
  // is drafted here only so the page renders for review. The DE/FI variants are literal
  // translations of the drafts, not authored copy — they are replaced in the same single copy pass.
  seoHomeTitle: "Football stats and match previews",
  seoHomeDesc: "Upcoming matches from every competition we cover.",
  homeNext: "Next matches",
  // Top players (#40). The block NAME is approved copy: plain nouns, matching the vocabulary
  // the page already uses, and a matched pair with "Top teams" so the two read as siblings.
  // "Player leaders" was rejected — "leader" collides with captaincy in football.
  homeTopPlayers: "Top players",
  // ⚠ APPROVED WORDING (#41), superseding an earlier approval. Both home blocks read one shape;
  // the previous string was "Season totals to date. The top player from each league: …", which
  // was only true mid-season.
  // "totals" is gone and nothing is lost: player boards are counts and team boards are rates, but
  // that distinction lives in the board HEADINGS (#41) — the team headings say "per match" and the
  // player headings are bare nouns, which is exactly what #41 says reads as a season total.
  // Three constraints the string still satisfies, recorded so a rewrite does not undo them: it
  // states the mechanic plainly and echoes the block's own name; it avoids "leader" for the reason
  // above; and it names no metric, because the sentence sits above all four boards and "top player"
  // carries every one of them equally.
  // The league list is the SHOWN group's members, injected from the data — not a fixed seven.
  homeTopPlayersIntro: "Current season. The top player from each league in the rankings: {leagues}.",
  homeTopTeams: "Top teams",
  // ⭐ APPROVED COPY (#41), the second half dictated verbatim in all three locales. Nothing here
  // is a draft and nothing is awaiting sign-off.
  //   · "in the rankings" says WHERE the pick comes from; no draft had it.
  //   · "leader" is still deliberately absent: "Player leaders / Team leaders" was turned down as
  //     the block name because "leader" collides with captaincy in football and translates
  //     awkwardly, and the spec records the objection applying to this sentence too.
  //   · The sentence sits above all four boards, so it names no metric.
  // ⛔ A comment here once said the opposite — it called the value below a wireframe draft still
  // awaiting approval while it was the approved wording, and it justified a "Season to date"
  // wording already rejected. Unapproved copy LOOKING approved and approved copy looking
  // unapproved are the same accumulate-instead-of-replace failure. Replaced, not amended.
  homeTopTeamsIntro: "Current season. The top team from each league in the rankings: {leagues}.",
  // A metric's second line: a value averaged over matches, or a share named by its count.
  perMatch: "per match",
  percentage: "percentage",
  homeNoFixtures: "No matches scheduled right now.",
  homeShowAll: "Show all {n}",
  homeShowLess: "Show less",
  showAllMetrics: "Show all metrics",
  // Competitions index page (#62 step 5) — category labels (competition_types.csv
  // label_i18n_key) and region labels (confederations.csv label_i18n_key). Only the keys the
  // live export actually uses (docs/wireframes/00_overview.md's binding rule): a
  // competition_type with zero onboarded competitions today has no key yet.
  compTypeDomesticLeague: "Domestic leagues",
  compTypeDomesticCup: "Domestic cups",
  compTypeContinentalCup: "Continental club cups",
  compTypeContinentalSuperCup: "Continental super cups",
  compTypeClubWorldCup: "Club World Cup",
  compTypeQualifying: "National team qualifiers",
  compTypeContinentalChampionship: "Continental championships",
  compTypeWorldChampionship: "World Cup",
  compTypeDomesticSuperCup: "Domestic super cups",
  compTypeClubQualifying: "Continental club qualifiers",
  compTypeIntercontinentalSuperCup: "Intercontinental Cup",
  compTypeClubFriendlyDomestic: "Domestic club friendlies",
  compTypeClubFriendlyInternational: "International club friendlies",
  compTypeNationalTeamFriendly: "National team friendlies",
  confedAfc: "Asia",
  confedCaf: "Africa",
  confedConcacaf: "North & Central America",
  confedConmebol: "South America",
  confedFifa: "World",
  confedOfc: "Oceania",
  confedUefa: "Europe",
  seoCompetitionsTitle: "All football competitions",
  seoCompetitionsDesc: "Every league, cup and international competition we cover, grouped by type and region.",
  seoTeamsTitle: "All football teams",
  seoTeamsDesc: "Every club and national team we cover: the top teams of each region, clubs by country and national teams by region.",
  teamsTopClubs: "Top clubs",
  teamsTopNational: "Top national teams",
  teamsClubsByCountry: "Clubs by country",
  teamsNationalByRegion: "National teams by region",
  teamsOtherClubs: "Other clubs",
  teamsCountOne: "{n} team",
  teamsCount: "{n} teams",
  // The competition HUB (singular), not the index above. Deliberately modest wording: the page is
  // a scaffold with no content blocks yet (#47), so a title promising a table, fixtures and
  // scorers would be a promise the page does not keep. Revisit the wording when #47 fills it.
  seoCompetitionTitle: "{competition}: Overview",
  seoCompetitionDesc: "Overview page for {competition}.",
  seoCompetitionFixturesTitle: "{competition}: Fixtures and results {season}",
  seoCompetitionFixturesDesc: "Every matchday of {competition} {season}: results so far and the fixtures to come, one matchday at a time.",
  seoMatchesTitle: "Football today: all matches, {date}",
  seoMatchDayTitle: "Football on {date}: all matches",
  seoMatchesDesc: "Every football match on {date} from {n} competitions: the kick-off time before the match, the result after it.",
  dayPickerAria: "Pick a day",
  seoCompetitionStatsTitle: "{competition}: Stats {season}",
  seoCompetitionStatsDesc: "The top teams and players of {competition} {season} on every stat: goals, {sotName}, passing, duels, defending, discipline and goalkeeping.",
  // The player page (#40 MR B). Same modest wording and the same reason as the competition hub
  // above: this is a scaffold with no content blocks, so the title promises nothing.
  // ⚠ THE CLUB IS IN THE TITLE FOR UNIQUENESS, not decoration. audit-seo check 5 requires titles to
  // be unique within a locale, and 1.6% of provider FULL names collide (site_architecture.md:93) —
  // which is also why the slug still carries the player id. The club disambiguates the two.
  seoPlayerTitle: "{player} ({club}): Overview",
  seoPlayerDesc: "Overview page for {player} of {club}.",
  filterAll: "All",
  filterClubs: "Clubs",
  filterNational: "National teams",
  filterByType: "Filter by type",
  filterByRegion: "Filter by region",
  filterAllTypes: "All types",
  filterAllRegions: "All regions",
  // The competition page (GitLab #129): the Overview tab and its blocks.
  compTabsAria: "Competition sections",
  compTabOverview: "Overview",
  compTabMatchdays: "Matchdays",
  compTabRounds: "Rounds",
  compTabRankings: "Rankings",
  compSeason: "Season {season}",
  compColPos: "#",
  compColPlayed: "P",
  compColWins: "W",
  compColDraws: "D",
  compColLosses: "L",
  compColGoals: "Goals",
  compColGoalDiff: "GD",
  compColPoints: "Pts",
  compSecTable: "Table",
  compSecSchedule: "Schedule",
  compPickerAria: "Pick a matchday",
  compNextTag: "Next",
  compTBC: "TBC",
  compTopMatch: "Top match",
  compSecDeserved: "{deservedName} table",
  compDeservedExplainer: "{deservedName} are the points a team's {sotdName} usually earns. {sotdNameStart} is the team's {sotName} minus its opponents' {sotName}. Teams with fewer points than deserved are better than the table says; teams with more are worse.",
  compSecTeamRankings: "Team rankings",
  compSecPlayerRankings: "Player rankings",
  compTeamRankingsIntro: "The leading teams {in} this season, metric by metric.",
  compPlayerRankingsIntro: "The leading players {in} this season, metric by metric.",
  compSecFacts: "The season in numbers",
  compFactGoalsPerMatch: "Goals per match",
  compFactGoalsInMatches: "{goals} goals in {matches} matches",
  compFactHomeWins: "Home wins",
  compFactOf: "{count} of {of}",
  compFactDrawsAway: "{draws} draws, {awayWins} away wins",
  compFactBiggestMargin: "Biggest margin",
  compFactMostGoals: "Most goals in a match",
  compFactLongestUnbeaten: "Longest unbeaten run",
  compFactLongestWinless: "Longest winless run",
  compFactMatches: "{n} matches",
  compFactMatchday: "Matchday {n}",
  roundMatchweek: "Matchweek {n}",
  roundWeek: "Week {n}",
  roundAperturaMatchday: "Apertura · Matchday {n}",
  roundClausuraMatchday: "Clausura · Matchday {n}",
  roundGroupStageMatchday: "Group stage · Matchday {n}",
  roundWcGroupMatchday: "Group stage · Matchday {n}",
  roundQualGroupMatchday: "Group stage · Matchday {n}",
  roundOcSecondRoundMatchday: "Second round · Matchday {n}",
  roundGroupMatchday: "Group {g} · Matchday {n}",
  roundLeaguePhaseMatchday: "League phase · Matchday {n}",
  roundLeagueStageMatchday: "League Stage · Matchday {n}",
  roundNationsLeagueMatchday: "League {g} · Matchday {n}",
  roundOf32: "Round of 32",
  roundWcOf32: "Round of 32",
  roundOf16: "Round of 16",
  roundOf: "Round of {n}",
  roundQuarterFinals: "Quarter-finals",
  roundQuarterfinalsAm: "Quarterfinals",
  roundSemiFinals: "Semi-finals",
  roundSemifinalsAm: "Semifinals",
  roundPlayoffSemiFinals: "Play-off semi-finals",
  roundIpSemiFinal: "Play-off Tournament semi-final",
  roundOcThirdRoundSemiFinals: "Third round semi-finals",
  roundFinal: "Final",
  roundPlayoffFinal: "Play-off final",
  roundIpFinal: "Play-off Tournament final",
  roundAsFifthRound: "Play-offs knockout stage",
  roundOcThirdRoundFinal: "Third round final",
  roundVlEuroFinal: "European play-off final",
  roundThirdPlace: "Third-place play-off",
  roundWcBronzeFinal: "Bronze final",
  roundThirdPlaceMatch: "Third Place Match",
  roundQualifyingRound1: "First qualifying round",
  roundQualifyingRound2: "Second qualifying round",
  roundQualifyingRound3: "Third qualifying round",
  roundOcFirstRound: "First round",
  roundOcFirstRoundFinal: "First round final",
  roundPlayoffRound: "Play-off round",
  roundKnockoutPlayoffs: "Knockout phase play-offs",
  roundAfcPreliminaryStage: "Preliminary Stage",
  roundPreliminaryRound1: "First preliminary round",
  roundPreliminaryRound2: "Second preliminary round",
  roundLiberStage1: "First stage",
  roundLiberStage2: "Second stage",
  roundLiberStage3: "Third stage",
  roundFirstRound: "First round",
  roundSecondRound: "Second round",
  roundPreliminaryRound: "Preliminary round",
  roundSeventhRound: "Seventh round",
  roundEighthRound: "Eighth round",
  roundFaQualifying1: "First Round Qualifying",
  roundFaQualifying2: "Second Round Qualifying",
  roundFaQualifying3: "Third Round Qualifying",
  roundFaQualifying4: "Fourth Round Qualifying",
  roundFaQualifying1Replay: "First Round Qualifying Replay",
  roundFaQualifying2Replay: "Second Round Qualifying Replay",
  roundFaQualifying3Replay: "Third Round Qualifying Replay",
  roundFaQualifying4Replay: "Fourth Round Qualifying Replay",
  roundFaFirstRoundProper: "First Round Proper",
  roundQualFirstRound: "First round",
  roundAsSecondRoundGroupMatchday: "Second round · Group {g} · Matchday {n}",
  roundAsThirdRoundMatchday: "Third round · Matchday {n}",
  roundAsPlayoffsMatchday: "Play-offs · Matchday {n}",
  roundCaFirstRound: "First Round",
  roundCaSecondRoundMatchday: "Second Round · Matchday {n}",
  roundCaFinalRoundMatchday: "Final Round · Matchday {n}",
  roundVlChampionshipMatchday: "Championship group · Matchday {n}",
  roundVlRelegationMatchday: "Relegation group · Matchday {n}",
  roundVlRelegationPlayoff: "Relegation play-off",
  compVs: "vs",
  playedFullTime: "Full time",
  playedAfterExtraTime: "After extra time",
  playedAfterPenalties: "After penalties",
  playedAwarded: "Awarded",
  awardNotPlayed: "The match was not played; the result was awarded.",
  awardPlayed: "Played {onPitch}; the result was awarded {awarded} afterwards.",
  awardAbandoned: "Abandoned at {onPitch}; the result was awarded {awarded}.",
  awardNotPlayedTo: "The match was not played; it was awarded to {team}.",
  awardPlayedTo: "Played {onPitch}; the match was awarded to {team} afterwards.",
  awardAbandonedTo: "Abandoned at {onPitch}; the match was awarded to {team}.",
  secGoals: "Goals",
  goalPenalty: "Penalty",
  goalOwnGoal: "Own goal",
  goalAssist: "Assist: {name}",
  goalsNoMinutes: "The minutes of these goals are not recorded.",
  goalsNotRecorded: "Goal scorers are not recorded for this round.",
  secMatchLeaders: "Match leaders",
  leadersIntro: "The match's most notable players, across both teams.",
  leadersNotRecorded: "The players' numbers are not recorded for this match.",
  leadersSideNotRecorded: "The numbers of {team}'s players are not recorded for this match.",
  secMatchStats: "Match stats",
  matchStatsIntro: "Each team's numbers in this match.",
  matchStatsNotRecorded: "The teams' numbers are not recorded for this match.",
  secLineups: "Line-ups",
  lineupSubstitutes: "Substitutes",
  lineupOff: "off {minute}",
  lineupOn: "on {minute} for {player}",
  lineupMinutes: "min",
  lineupsNotRecorded: "The line-ups are not recorded for this match.",
};

const DE: Dict = {
  crumbHome: "Startseite",
  crumbMatches: "Spiele",
  eyebrowPreview: "Spielvorschau",
  secForm: "Formvergleich",
  secRecent: "Letzte Spiele",
  secPlayers: "Spieler im Fokus",
  secH2H: "Direkter Vergleich",
  secAbout: "Über dieses Spiel",
  secExplore: "Entdecken",
  segLast5: "Letzte 5",
  segSeason: "Diese Saison",
  scopeAllComps: "alle Wettbewerbe",
  vs: "gegen",
  pts: "Pkt.",
  goals: "Tore",
  assists: "Vorlagen",
  saves: "Paraden",
  incl: "inkl.",
  throughMatchday: "bis Spieltag {n}",
  lastSeason: "letzte Saison ({year})",
  playersWindow: "Letzte 5 Spiele",
  statsCoverage: "Statistik aus {a} von {b} Spielen",
  meetings: "Begegnungen",
  draws: "Remis",
  goalsWord: "Tore",
  lastMeeting: "Zuletzt",
  firstMeeting: "Erstes Aufeinandertreffen",
  h2hLastDrawn: "Das letzte Duell endete unentschieden.",
  h2hLastWon: "{club} gewann das letzte Duell.",
  h2hBothDrawn: "Die letzten beiden Duelle endeten unentschieden.",
  h2hAllDrawn: "Die letzten {n} Duelle endeten alle unentschieden.",
  h2hWonBoth: "{club} gewann die letzten beiden Duelle.",
  h2hWonAll: "{club} gewann alle letzten {n} Duelle.",
  h2hWonSomeOneDrawn: "{club} gewann {won} der letzten {n} Duelle, 1 endete unentschieden.",
  h2hWonSomeDrawn: "{club} gewann {won} der letzten {n} Duelle, {d} endeten unentschieden.",
  h2hSplit: "Von den letzten {n} Duellen gewann {home} {w} und {away} {l}.",
  h2hSplitOneDrawn: "Von den letzten {n} Duellen gewann {home} {w} und {away} {l}, 1 endete unentschieden.",
  h2hSplitDrawn: "Von den letzten {n} Duellen gewann {home} {w} und {away} {l}, {d} endeten unentschieden.",
  h2hNone: "Keine Duelle erfasst.",
  formIntro: "Formwerte aus den letzten 5 Spielen jedes Teams in allen Wettbewerben.",
  formIntroPrev: "Formwerte aus den letzten 5 Spielen jedes Teams in allen Wettbewerben; vor dem ersten Spiel in der {competition} aus der letzten Saison dort.",
  compIn: "in der {competition}",
  compInMasculine: "im {competition}",
  playersIntro: "Die besten Spieler jedes Teams {in} in dieser Saison, nach Toren plus Vorlagen.",
  playersIntroPrev: "Die besten Spieler jedes Teams {in} nach Toren plus Vorlagen; vor dem ersten Spiel dort aus der letzten Saison.",
  haHome: "H",
  haAway: "A",
  noRecentForm: "Keine aktuellen Spiele",
  noMatchStats: "Keine Spielstatistik",
  timeTBD: "Uhrzeit offen",
  table: "Tabelle",
  fullH2H: "Kompletter Vergleich",
  footnote: "Beispieldaten · v2-Vorschau ({brand})",
  aboutWithH2h: "{home} gegen {away} · {round}. Die Klubs trafen bereits {meetings} Mal aufeinander: {record}.",
  aboutNoH2h: "{home} gegen {away} · {round}.",
  posF: "Angriff", posM: "Mittelfeld", posD: "Abwehr", posG: "Tor",
  // --- team page (Overview) ---
  crumbTeams: "Mannschaften",
  crumbAria: "Brotkrümelnavigation",
  tabsAria: "Mannschaftsbereiche",
  founded: "Gegründet",
  tabOverview: "Übersicht",
  tabPerformance: "Leistung",
  tabSquad: "Kader",
  teamPerfIntro: "{competition} {season}: {team} im Vergleich mit den anderen Mannschaften und mit der Vorsaison. Andere Wettbewerbe sind nicht enthalten.",
  teamLeaguePhase: "Ligaphase",
  teamThrough: "Weiter",
  teamKnockedOut: "Ausgeschieden",
  teamWinners: "Sieger",
  teamHighsLows: "Höhen und Tiefen",
  teamBiggestWin: "Höchster Sieg",
  teamHeaviestDefeat: "Höchste Niederlage",
  teamVsHome: "gegen {opponent}",
  teamAtAway: "bei {opponent}",
  teamUpcoming: "Kommende Spiele",
  teamResults: "Ergebnisse",
  teamStanding: "Tabellenstand",
  teamPosition: "Platz",
  teamSeasonBefore: "Vorsaison: {value}",
  teamAfterMatches: "{competition}, nach {n} Spielen",
  teamOtherTeams: "Übrige Klubs der Liga",
  teamScatterAria: "Punkte und Torschussdifferenz pro Spiel aller Mannschaften der Liga, mit der Linie der verdienten Punkte.",
  teamVsLeague: "Im Vergleich zur Liga",
  teamVsLeagueIntro: "Alle Werte im Vergleich mit den übrigen Klubs der Liga in dieser Saison. Der Median teilt die Liga in zwei Hälften: Die eine Hälfte der Klubs liegt darüber, die andere darunter.",
  teamLeagueMedian: "Liga-Median",
  teamBetterLeft: "← besser",
  teamBetterRight: "besser →",
  teamVsLastSeason: "Im Vergleich zur Vorsaison",
  teamVsLastSeasonIntro: "Beide Spielzeiten werden über ihre ersten {n} Spiele verglichen.",
  teamThisSeasonHead: "Diese Saison",
  teamLastSeasonHead: "Vorsaison",
  teamTrend: "Trend",
  teamTrendBetter: "besser als in der Vorsaison",
  teamTrendWorse: "schlechter als in der Vorsaison",
  teamTrendSame: "wie in der Vorsaison",
  appearanceCountOne: "{n} Einsatz",
  appearanceCount: "{n} Einsätze",
  filterAllCompetitions: "Alle Wettbewerbe",
  filterByCompetition: "Nach Wettbewerb filtern",
  comingTitle: "Demnächst",
  // German keeps ONE sentence where EN and FI take two. The em dash here was a stylistic pause
  // between a subject and its only finite verb, not a clause break: splitting it leaves "Kommt
  // mit dem nächsten Release." — a finite verb with no subject, which German reads as an
  // imperative. EN "Landing…" and FI "Tulossa…" are non-finite fragments and split safely.
  comingPerformance: "Jede Kennzahl im Vergleich zur Liga und zur Vorsaison kommt mit dem nächsten Release.",
  comingSquad: "Der komplette Kader mit Einsatzminuten und Scorerwerten je Spieler kommt mit dem nächsten Release.",
  // squad tab
  squadGk: "Torhüter", squadDef: "Abwehr", squadMid: "Mittelfeld", squadFwd: "Angriff", squadOther: "Sonstige",
  seasonToDate: "Saison bis dato",
  goalOne: "Tor", assistOne: "Vorlage",
  median: "Median",
  secDeserved: "Verdient vs. tatsächlich",

  // APPOSITIVE, not a preposition. The first version read "{team} in {competition}: …", justified as
  // avoiding the gender problem (die Bundesliga / der DFB-Pokal / die Premier League — a template
  // cannot inflect an article for a competition it does not know). That was a misdiagnosis: German
  // "in" before a named competition ALWAYS takes a case-marked article, so dropping it did not make
  // the sentence gender-neutral, it made it ungrammatical on every German team page. The
  // PARENTHETICAL form needs no article and no case, and all three locales now share it.
  // Parentheses in the description, not the en dash Gemini supplied: same anti-AI-tell reason, and
  // they sidestep the article problem too — "(Premier League)" needs no case-marked article, where
  // "in der/im {competition}" would need one the template cannot know.
  // "Kader" and "Spiele" are reused verbatim from the approved description below, so the two
  // surfaces name the same things with the same words.
  seoTeamTitle: "{team}: Statistiken, Form, Kader & Spiele",
  seoTeamDesc: "{team} ({competition}): Form, Spiele, Kader und Saisonstatistiken.",
  // "gegen" stays, and the reason is worth recording. I briefly changed it to "vs." to claw back
  // 3 characters after a real pairing ("Wolverhampton Wanderers gegen Manchester United | Premier
  // League", ~624px vs the ~600px budget) overran. The gate rejected that instantly: this title is
  // made ONLY of proper nouns, so once "gegen" becomes "vs." the German and Finnish titles are
  // BYTE-IDENTICAL and there is nothing left to tell the locales apart.
  // The general point: a title of pure proper nouns cannot be localised. "gegen" is the entire
  // German signal in this string, so it is not spare budget — it is the localisation.
  // The overrun on that one extreme pairing is accepted; the competition truncates, which is the
  // least-bad thing to lose, and the team names a reader searched for stay visible.
  // "gegen" becomes a dash: it is what German football writing uses for a pairing, and it is also
  // what gets DE under the limit (2 of 26 competitions failed with "gegen", 0 with the dash).
  // Worst real fixture: 595px, inside the 600px budget. See the EN entry for the full reasoning.
  seoFixtureTitle: "{home} - {away}, {date}",
  // --- chrome (site-wide header/footer, #825) ---
  navCompetitions: "Wettbewerbe",
  navMatches: "Spiele",
  navTeams: "Mannschaften",
  navPlayers: "Spieler",
  navStandings: "Tabelle",
  navStatistics: "Statistiken",
  mainNavAria: "Hauptnavigation",
  searchPlaceholder: "Mannschaften, Spieler suchen…",
  searchAria: "Suche",
  themeToggleAria: "Design umschalten",
  menuAria: "Menü",
  footerAbout: "Über uns",
  footerImprintPending: "Impressum (in Vorbereitung)",
  footerDataSource: "Daten: API-Football",
  // --- landing (#367). PLACEHOLDER, see the EN block.
  seoHomeTitle: "Fußballstatistiken und Spielvorschauen",
  seoHomeDesc: "Kommende Spiele aus allen Wettbewerben, die wir abdecken.",
  homeNext: "Nächste Spiele",
  homeTopPlayers: "Top-Spieler",
  // ⚠ `Der Top-Spieler` is grammatically MASCULINE and blocks a women's competition: including
  // women's teams means changing this string properly.
  // `Die Top-Mannschaft` below is NOT affected — Mannschaft is the standard German
  // word for a women's team too. EN and FI are unaffected; Finnish has no grammatical gender.
  homeTopPlayersIntro: "Aktuelle Saison. Der Top-Spieler jeder Liga in den Ranglisten: {leagues}.",
  homeTopTeams: "Top-Mannschaften",
  // Approved copy (#41). It mirrors the DE players line above — both approved together — and
  // avoids "Führende", the German trap the "leader" rejection points at.
  homeTopTeamsIntro: "Aktuelle Saison. Die Top-Mannschaft jeder Liga in den Ranglisten: {leagues}.",
  perMatch: "pro Spiel",
  percentage: "in Prozent",
  homeNoFixtures: "Derzeit sind keine Spiele angesetzt.",
  homeShowAll: "Alle {n} anzeigen",
  homeShowLess: "Weniger anzeigen",
  showAllMetrics: "Alle Kennzahlen anzeigen",
  compTypeDomesticLeague: "Nationale Ligen",
  compTypeDomesticCup: "Nationale Pokale",
  compTypeContinentalCup: "Kontinentale Vereinspokale",
  compTypeContinentalSuperCup: "Kontinentale Superpokale",
  compTypeClubWorldCup: "Klub-Weltmeisterschaft",
  compTypeQualifying: "Nationalmannschafts-Qualifikation",
  compTypeContinentalChampionship: "Kontinentale Meisterschaften",
  compTypeWorldChampionship: "Weltmeisterschaft",
  compTypeDomesticSuperCup: "Nationale Superpokale",
  compTypeClubQualifying: "Kontinentale Vereinsqualifikation",
  compTypeIntercontinentalSuperCup: "Interkontinental-Pokal",
  compTypeClubFriendlyDomestic: "Nationale Vereinsfreundschaftsspiele",
  compTypeClubFriendlyInternational: "Internationale Vereinsfreundschaftsspiele",
  compTypeNationalTeamFriendly: "Länderspiel-Freundschaftsspiele",
  confedAfc: "Asien",
  confedCaf: "Afrika",
  confedConcacaf: "Nord- und Mittelamerika",
  confedConmebol: "Südamerika",
  confedFifa: "Welt",
  confedOfc: "Ozeanien",
  confedUefa: "Europa",
  seoCompetitionsTitle: "Alle Fußballwettbewerbe",
  seoCompetitionsDesc: "Jede Liga, jeder Pokal und jeder internationale Wettbewerb, den wir abdecken, gruppiert nach Art und Region.",
  seoTeamsTitle: "Alle Fußballmannschaften",
  seoTeamsDesc: "Jeder Verein und jede Nationalmannschaft, die wir abdecken: die besten Teams jeder Region, Vereine nach Land und Nationalmannschaften nach Region.",
  teamsTopClubs: "Top-Vereine",
  teamsTopNational: "Top-Nationalmannschaften",
  teamsClubsByCountry: "Vereine nach Land",
  teamsNationalByRegion: "Nationalmannschaften nach Region",
  teamsOtherClubs: "Weitere Vereine",
  teamsCountOne: "{n} Mannschaft",
  teamsCount: "{n} Mannschaften",
  seoCompetitionTitle: "{competition}: Überblick",
  seoCompetitionDesc: "Überblicksseite für {competition}.",
  seoCompetitionFixturesTitle: "{competition}: Spielplan {season}",
  seoCompetitionFixturesDesc: "Alle Spieltage von {competition} {season}: die bisherigen Ergebnisse und die kommenden Spiele, ein Spieltag nach dem anderen.",
  seoMatchesTitle: "Fußball heute: alle Spiele, {date}",
  seoMatchDayTitle: "Fußball am {date}: alle Spiele",
  seoMatchesDesc: "Alle Fußballspiele am {date} aus {n} Wettbewerben: vor dem Spiel die Anstoßzeit, danach das Ergebnis.",
  dayPickerAria: "Tag wählen",
  seoCompetitionStatsTitle: "{competition}: Statistiken {season}",
  seoCompetitionStatsDesc: "Die besten Mannschaften und Spieler von {competition} {season} in jeder Statistik: Tore, {sotName}, Passspiel, Zweikämpfe, Defensive, Disziplin und Torwartspiel.",
  seoPlayerTitle: "{player} ({club}): Überblick",
  seoPlayerDesc: "Überblicksseite für {player} von {club}.",
  filterAll: "Alle",
  filterClubs: "Vereine",
  filterNational: "Nationalmannschaften",
  filterByType: "Nach Art filtern",
  filterByRegion: "Nach Region filtern",
  filterAllTypes: "Alle Arten",
  filterAllRegions: "Alle Regionen",
  compTabsAria: "Wettbewerbsbereiche",
  compTabOverview: "Übersicht",
  compTabMatchdays: "Spieltage",
  compTabRounds: "Runden",
  compTabRankings: "Ranglisten",
  compSeason: "Saison {season}",
  compColPos: "#",
  compColPlayed: "Sp.",
  compColWins: "S",
  compColDraws: "U",
  compColLosses: "N",
  compColGoals: "Tore",
  compColGoalDiff: "Diff.",
  compColPoints: "Pkt.",
  compSecTable: "Tabelle",
  compSecSchedule: "Spielplan",
  compPickerAria: "Spieltag wählen",
  compNextTag: "Nächster",
  compTBC: "Offen",
  compTopMatch: "Topspiel",
  compSecDeserved: "Tabelle nach verdienten Punkten",
  compDeservedExplainer: "{deservedName} sind die Punkte, die eine Mannschaft mit ihrer {sotdName} in der Regel holt. Die {sotdName} ist die Zahl der eigenen {sotName} minus die der Gegner. Teams mit weniger Punkten als verdient sind besser, als es die Tabelle zeigt; Teams mit mehr sind schlechter.",
  compSecTeamRankings: "Mannschafts-Ranglisten",
  compSecPlayerRankings: "Spieler-Ranglisten",
  compTeamRankingsIntro: "Die besten Mannschaften {in} in dieser Saison, Kennzahl für Kennzahl.",
  compPlayerRankingsIntro: "Die besten Spieler {in} in dieser Saison, Kennzahl für Kennzahl.",
  compSecFacts: "Die Saison in Zahlen",
  compFactGoalsPerMatch: "Tore pro Spiel",
  compFactGoalsInMatches: "{goals} Tore in {matches} Spielen",
  compFactHomeWins: "Heimsiege",
  compFactOf: "{count} von {of}",
  compFactDrawsAway: "{draws} Unentschieden, {awayWins} Auswärtssiege",
  compFactBiggestMargin: "Höchster Sieg",
  compFactMostGoals: "Torreichstes Spiel",
  compFactLongestUnbeaten: "Längste Serie ohne Niederlage",
  compFactLongestWinless: "Längste Serie ohne Sieg",
  compFactMatches: "{n} Spiele",
  compFactMatchday: "{n}. Spieltag",
  roundMatchweek: "{n}. Spieltag",
  roundWeek: "{n}. Spieltag",
  roundAperturaMatchday: "Apertura, {n}. Spieltag",
  roundClausuraMatchday: "Clausura, {n}. Spieltag",
  roundGroupStageMatchday: "{n}. Gruppenspieltag",
  roundWcGroupMatchday: "Vorrunde, {n}. Spieltag",
  roundQualGroupMatchday: "{n}. Gruppenspieltag",
  roundOcSecondRoundMatchday: "2. Runde, {n}. Spieltag",
  roundGroupMatchday: "Gruppe {g}, {n}. Spieltag",
  roundLeaguePhaseMatchday: "Ligaphase, {n}. Spieltag",
  roundLeagueStageMatchday: "Ligaphase, {n}. Spieltag",
  roundNationsLeagueMatchday: "Liga {g}, {n}. Spieltag",
  roundOf32: "Sechzehntelfinale",
  roundWcOf32: "Sechzehntelfinale",
  roundOf16: "Achtelfinale",
  roundOf: "Runde der letzten {n}",
  roundQuarterFinals: "Viertelfinale",
  roundQuarterfinalsAm: "Viertelfinale",
  roundSemiFinals: "Halbfinale",
  roundSemifinalsAm: "Halbfinale",
  roundPlayoffSemiFinals: "Play-off-Halbfinale",
  roundIpSemiFinal: "Halbfinale",
  roundOcThirdRoundSemiFinals: "Halbfinale",
  roundFinal: "Finale",
  roundPlayoffFinal: "Play-off-Finale",
  roundIpFinal: "Finale",
  roundAsFifthRound: "5. Runde",
  roundOcThirdRoundFinal: "Finale",
  roundVlEuroFinal: "Europapokal-Play-off-Finale",
  roundThirdPlace: "Spiel um Platz 3",
  roundWcBronzeFinal: "Spiel um Platz 3",
  roundThirdPlaceMatch: "Spiel um Platz 3",
  roundQualifyingRound1: "1. Qualifikationsrunde",
  roundQualifyingRound2: "2. Qualifikationsrunde",
  roundQualifyingRound3: "3. Qualifikationsrunde",
  roundOcFirstRound: "1. Runde, Halbfinale",
  roundOcFirstRoundFinal: "1. Runde, Finale",
  roundPlayoffRound: "Play-off-Runde",
  roundKnockoutPlayoffs: "Play-offs der K.-o.-Phase",
  roundAfcPreliminaryStage: "Qualifikationsrunde",
  roundPreliminaryRound1: "1. Qualifikationsrunde",
  roundPreliminaryRound2: "2. Qualifikationsrunde",
  roundLiberStage1: "1. Qualifikationsrunde",
  roundLiberStage2: "2. Qualifikationsrunde",
  roundLiberStage3: "3. Qualifikationsrunde",
  roundFirstRound: "1. Runde",
  roundSecondRound: "2. Runde",
  roundPreliminaryRound: "Vorrunde",
  roundSeventhRound: "7. Runde",
  roundEighthRound: "8. Runde",
  roundFaQualifying1: "1. Qualifikationsrunde",
  roundFaQualifying2: "2. Qualifikationsrunde",
  roundFaQualifying3: "3. Qualifikationsrunde",
  roundFaQualifying4: "4. Qualifikationsrunde",
  roundFaQualifying1Replay: "Wiederholungsspiel, 1. Qualifikationsrunde",
  roundFaQualifying2Replay: "Wiederholungsspiel, 2. Qualifikationsrunde",
  roundFaQualifying3Replay: "Wiederholungsspiel, 3. Qualifikationsrunde",
  roundFaQualifying4Replay: "Wiederholungsspiel, 4. Qualifikationsrunde",
  roundFaFirstRoundProper: "1. Runde",
  roundQualFirstRound: "1. Runde",
  roundAsSecondRoundGroupMatchday: "2. Runde, Gruppe {g}, {n}. Spieltag",
  roundAsThirdRoundMatchday: "3. Runde, {n}. Spieltag",
  roundAsPlayoffsMatchday: "4. Runde, {n}. Spieltag",
  roundCaFirstRound: "1. Runde",
  roundCaSecondRoundMatchday: "2. Runde, {n}. Spieltag",
  roundCaFinalRoundMatchday: "Finalrunde, {n}. Spieltag",
  roundVlChampionshipMatchday: "Meisterrunde, {n}. Spieltag",
  roundVlRelegationMatchday: "Abstiegsrunde, {n}. Spieltag",
  roundVlRelegationPlayoff: "Relegation",
  compVs: "gegen",
  playedFullTime: "Spielende",
  playedAfterExtraTime: "Nach Verlängerung",
  playedAfterPenalties: "Nach Elfmeterschießen",
  playedAwarded: "Gewertet",
  awardNotPlayed: "Das Spiel wurde nicht ausgetragen; das Ergebnis wurde gewertet.",
  awardPlayed: "Gespielt {onPitch}; nachträglich mit {awarded} gewertet.",
  awardAbandoned: "Abgebrochen beim Stand von {onPitch}; mit {awarded} gewertet.",
  awardNotPlayedTo: "Das Spiel wurde nicht ausgetragen und für {team} gewertet.",
  awardPlayedTo: "Gespielt {onPitch}; nachträglich für {team} gewertet.",
  awardAbandonedTo: "Abgebrochen beim Stand von {onPitch}; für {team} gewertet.",
  secGoals: "Tore",
  goalPenalty: "Elfmeter",
  goalOwnGoal: "Eigentor",
  goalAssist: "Vorlage: {name}",
  goalsNoMinutes: "Die Spielminuten dieser Tore sind nicht erfasst.",
  goalsNotRecorded: "Die Torschützen dieser Runde sind nicht erfasst.",
  secMatchLeaders: "Bestwerte",
  leadersIntro: "Die auffälligsten Spieler des Spiels, aus beiden Teams.",
  leadersNotRecorded: "Die Spielerwerte sind für dieses Spiel nicht erfasst.",
  leadersSideNotRecorded: "Die Werte der Spieler von {team} sind für dieses Spiel nicht erfasst.",
  secMatchStats: "Spielstatistik",
  matchStatsIntro: "Die Werte beider Teams in diesem Spiel.",
  matchStatsNotRecorded: "Die Teamwerte sind für dieses Spiel nicht erfasst.",
  secLineups: "Aufstellungen",
  lineupSubstitutes: "Einwechslungen",
  lineupOff: "ausgewechselt {minute}",
  lineupOn: "eingewechselt {minute} für {player}",
  lineupMinutes: "Min.",
  lineupsNotRecorded: "Die Aufstellungen sind für dieses Spiel nicht erfasst.",
};

const FI: Dict = {
  crumbHome: "Etusivu",
  crumbMatches: "Ottelut",
  eyebrowPreview: "Otteluennakko",
  // "kunto", not "muoto": muoto is shape/format, and the football sense of form is kunto —
  // corroborated by the MVP corpus, which renders "form window" as `kuntojakso`
  // (site/i18n/fi.json). The #867 correction, extended to this key; the deferral noted at
  // seoTeamTitle below is now closed.
  secForm: "Kuntovertailu",
  secRecent: "Viimeisimmät ottelut",
  secPlayers: "Seurattavat pelaajat",
  secH2H: "Keskinäiset ottelut",
  secAbout: "Tietoa ottelusta",
  secExplore: "Tutustu",
  segLast5: "Viimeiset 5",
  segSeason: "Tällä kaudella",
  scopeAllComps: "kaikki kilpailut",
  vs: "vs",
  pts: "pistettä",
  goals: "maalia",
  assists: "syöttöä",
  saves: "torjuntaa",
  incl: "ml.",
  throughMatchday: "kierrokseen {n} asti",
  lastSeason: "viime kausi ({year})",
  playersWindow: "5 viimeistä ottelua",
  statsCoverage: "tilastot {a}/{b} ottelusta",
  meetings: "kohtaamista",
  draws: "tasapeliä",
  goalsWord: "maalia",
  lastMeeting: "Viimeksi",
  firstMeeting: "Ensimmäinen kohtaaminen",
  h2hLastDrawn: "Edellinen kohtaaminen päättyi tasan.",
  h2hLastWon: "{club} voitti edellisen kohtaamisen.",
  h2hBothDrawn: "Kaksi edellistä kohtaamista päättyivät tasan.",
  h2hAllDrawn: "Kaikki {n} edellistä kohtaamista päättyivät tasan.",
  h2hWonBoth: "{club} voitti kaksi edellistä kohtaamista.",
  h2hWonAll: "{club} voitti kaikki {n} edellistä kohtaamista.",
  h2hWonSomeOneDrawn: "{club} voitti {n} edellisestä kohtaamisesta {won}, ja 1 päättyi tasan.",
  h2hWonSomeDrawn: "{club} voitti {n} edellisestä kohtaamisesta {won}, ja {d} päättyi tasan.",
  h2hSplit: "{n} edellisestä kohtaamisesta {home} voitti {w} ja {away} {l}.",
  h2hSplitOneDrawn: "{n} edellisestä kohtaamisesta {home} voitti {w} ja {away} {l}, ja 1 päättyi tasan.",
  h2hSplitDrawn: "{n} edellisestä kohtaamisesta {home} voitti {w} ja {away} {l}, ja {d} päättyi tasan.",
  h2hNone: "Ei kirjattuja kohtaamisia.",
  formIntro: "Kuntoluvut kunkin joukkueen 5 viimeisestä ottelusta kaikissa kilpailuissa.",
  formIntroPrev: "Kuntoluvut kunkin joukkueen 5 viimeisestä ottelusta kaikissa kilpailuissa; ennen ensimmäistä ottelua sarjassa {competition} edelliseltä kaudelta siellä.",
  compIn: "sarjassa {competition}",
  compInMasculine: "sarjassa {competition}",
  playersIntro: "Kunkin joukkueen parhaat pelaajat {in} tällä kaudella, maalien ja syöttöjen mukaan.",
  playersIntroPrev: "Kunkin joukkueen parhaat pelaajat {in} maalien ja syöttöjen mukaan; ennen ensimmäistä ottelua edelliseltä kaudelta.",
  haHome: "K",
  haAway: "V",
  noRecentForm: "Ei viimeaikaisia otteluita",
  noMatchStats: "Ei ottelutilastoja",
  timeTBD: "Aika auki",
  table: "Sarjataulukko",
  fullH2H: "Kaikki kohtaamiset",
  footnote: "Esimerkkidata · v2-esikatselu ({brand})",
  // "–" not "vs": the Finnish values were byte-identical to the English ones, so two of three
  // locales shipped the same <meta description>. Caught only after the cross-locale check was
  // tightened to fail on any GROUP of locales sharing a value rather than on all three matching —
  // the weaker form saw German differ and concluded the template was working.
  // "vs." to match this locale's own fixture TITLE. These were once switched to an en dash on the
  // unverified claim that Finnish football writing prefers one; the validated source uses "vs.",
  // and the page was contradicting itself — title "Palmeiras vs. Atletico-MG", description
  // "Palmeiras – Atletico-MG".
  // ⚠ RESIDUAL: this now differs from the EN string only by the full stop after "vs". The audit's
  // byte-identical check passes, but only just, and passing it is not the same as being localised.
  // A real Finnish description is copy, so it is the product owner's call (§10), not a quiet fix.
  aboutWithH2h: "{home} vs. {away} · {round}. Joukkueet ovat kohdanneet {meetings} kertaa: {record}.",
  aboutNoH2h: "{home} vs. {away} · {round}.",
  posF: "Hyökkäys", posM: "Keskikenttä", posD: "Puolustus", posG: "Maalivahti",
  // --- team page (Overview) ---
  crumbTeams: "Joukkueet",
  crumbAria: "Murupolku",
  tabsAria: "Joukkueen osiot",
  founded: "Perustettu",
  tabOverview: "Yleiskatsaus",
  tabPerformance: "Suoritus",
  tabSquad: "Kokoonpano",
  teamPerfIntro: "{competition} {season}: {team} verrattuna muihin joukkueisiin ja edelliseen kauteen. Muut kilpailut eivät ole mukana.",
  teamLeaguePhase: "Liigavaihe",
  teamThrough: "Jatkoon",
  teamKnockedOut: "Pudonnut",
  teamWinners: "Voittaja",
  teamHighsLows: "Ylä- ja alamäet",
  teamBiggestWin: "Suurin voitto",
  teamHeaviestDefeat: "Suurin tappio",
  teamVsHome: "kotona: {opponent}",
  teamAtAway: "vieraissa: {opponent}",
  teamUpcoming: "Tulevat ottelut",
  teamResults: "Tulokset",
  teamStanding: "Sarjatilanne",
  teamPosition: "Sijoitus",
  teamSeasonBefore: "Edellinen kausi: {value}",
  teamAfterMatches: "{competition}, {n} ottelun jälkeen",
  teamOtherTeams: "Sarjan muut joukkueet",
  teamScatterAria: "Sarjan kaikkien joukkueiden pisteet ja maalilaukausero per ottelu sekä ansaittujen pisteiden viiva.",
  teamVsLeague: "Verrattuna sarjaan",
  teamVsLeagueIntro: "Kaikkia lukuja verrataan sarjan muihin joukkueisiin tällä kaudella. Mediaani jakaa sarjan kahtia: puolet joukkueista on sen yläpuolella, puolet alapuolella.",
  teamLeagueMedian: "Sarjan mediaani",
  teamBetterLeft: "← parempi",
  teamBetterRight: "parempi →",
  teamVsLastSeason: "Verrattuna edelliskauteen",
  teamVsLastSeasonIntro: "Kausia verrataan kummankin {n} ensimmäisen ottelun osalta.",
  teamThisSeasonHead: "Tämä kausi",
  teamLastSeasonHead: "Viime kausi",
  teamTrend: "Suunta",
  teamTrendBetter: "parempi kuin edellisellä kaudella",
  teamTrendWorse: "huonompi kuin edellisellä kaudella",
  teamTrendSame: "sama kuin edellisellä kaudella",
  appearanceCountOne: "{n} ottelu",
  appearanceCount: "{n} ottelua",
  filterAllCompetitions: "Kaikki kilpailut",
  filterByCompetition: "Suodata kilpailun mukaan",
  comingTitle: "Tulossa",
  comingPerformance: "Jokainen tunnusluku sarjaan ja viime kauteen verrattuna. Tulossa seuraavassa julkaisussa.",
  comingSquad: "Koko kokoonpano pelaajakohtaisine peliminuutteineen ja tehopisteineen. Tulossa seuraavassa julkaisussa.",
  // squad tab
  squadGk: "Maalivahdit", squadDef: "Puolustajat", squadMid: "Keskikenttäpelaajat", squadFwd: "Hyökkääjät", squadOther: "Muut",
  seasonToDate: "kausi tähän mennessä",
  goalOne: "maali", assistOne: "syöttö",
  median: "Mediaani",
  secDeserved: "Ansaittu vs. toteutunut",

  // Finnish takes an appositive rather than a genitive: a proper noun cannot be inflected from a
  // template, so "{team}: ..." (not "{team}n tilastot") is the only form that stays grammatical
  // for every club name.
  // Supplied copy (§10 — user-visible copy is the product owner's), verbatim. "kunto", not
  // "muoto": muoto is shape/format, and the football sense of form is kunto — corroborated by the
  // MVP corpus, which renders "form window" as `kuntojakso` (site/i18n/fi.json). `secForm` above
  // carried the same error and is now `Kuntovertailu`, so that deferral is closed.
  // "ja" in the team title and "&" in the fixture title are both supplied choices, kept as
  // written; only the length changed.
  seoTeamTitle: "{team}: tilastot, kunto, kokoonpano ja ottelut",
  // Was "{team} sarjassa {competition}: …". `sarjassa` is inessive and governs a case the bare
  // borrowed league name cannot carry ("Premier Leaguessa" / "Valioliigassa"), so the template read
  // as machine translation. Parentheses instead: no case, no inflection, and they work for a
  // league name in any language. Same form as the EN and DE descriptions.
  seoTeamDesc: "{team} ({competition}): kunto, ottelut, kokoonpano ja kauden tilastot.",
  // The capital K is supplied, verbatim. The previous note here said not to swap "vs." for an en
  // dash "without a Finnish source" — THE SOURCE NOW EXISTS: Yle and MTV Uutiset pair
  // Veikkausliiga teams as "KuPS–HJK", tight en dash, no spaces. That is also what gets FI under
  // the limit: "vs." overflowed by 1px on one competition (661 against a 660 hard cap), the tight
  // en dash lands at 634px. Approved with the source on the table.
  // Worst real fixture: 573px, the widest headroom of the three. See the EN entry for the reasoning.
  seoFixtureTitle: "{home}–{away}, {date}",
  // --- chrome (site-wide header/footer, #825) ---
  navCompetitions: "Kilpailut",
  navMatches: "Ottelut",
  navTeams: "Joukkueet",
  navPlayers: "Pelaajat",
  navStandings: "Sarjataulukko",
  navStatistics: "Tilastot",
  mainNavAria: "Päänavigaatio",
  searchPlaceholder: "Hae joukkueita, pelaajia…",
  searchAria: "Haku",
  themeToggleAria: "Vaihda teema",
  menuAria: "Valikko",
  footerAbout: "Tietoa",
  footerImprintPending: "Vastuutiedot (tulossa)",
  // `Tietolähde` is the validated corpus's own term for "data source" ("Tietolähde ei
  // toimittanut tätä arvoa", site/i18n/fi.json), so this is a real translation rather than the
  // English string left in place.
  footerDataSource: "Tietolähde: API-Football",
  // --- landing (#367). PLACEHOLDER, see the EN block.
  seoHomeTitle: "Jalkapallotilastot ja otteluennakot",
  seoHomeDesc: "Tulevat ottelut kaikista kattamistamme kilpailuista.",
  homeNext: "Seuraavat ottelut",
  homeTopPlayers: "Kärkipelaajat",
  homeTopPlayersIntro: "Tämä kausi. Kunkin sarjan kärkipelaaja ranking-listoilla: {leagues}.",
  homeTopTeams: "Kärkijoukkueet",
  // Approved copy (#41), mirroring the FI players line above — `kärkipelaaja` there,
  // `kärkijoukkue` here.
  homeTopTeamsIntro: "Tämä kausi. Kunkin sarjan kärkijoukkue ranking-listoilla: {leagues}.",
  perMatch: "ottelua kohden",
  percentage: "prosentteina",
  homeNoFixtures: "Ei otteluita tällä hetkellä.",
  homeShowAll: "Näytä kaikki {n}",
  homeShowLess: "Näytä vähemmän",
  showAllMetrics: "Näytä kaikki tunnusluvut",
  compTypeDomesticLeague: "Kansalliset sarjat",
  compTypeDomesticCup: "Kansalliset cupit",
  compTypeContinentalCup: "Mantereiden seuracupit",
  compTypeContinentalSuperCup: "Mantereiden supercupit",
  compTypeClubWorldCup: "Seurojen MM-kisat",
  compTypeQualifying: "Maajoukkueiden karsinnat",
  compTypeContinentalChampionship: "Mantereiden mestaruuskilpailut",
  compTypeWorldChampionship: "MM-kisat",
  compTypeDomesticSuperCup: "Kansalliset supercupit",
  compTypeClubQualifying: "Mantereiden seurakarsinnat",
  compTypeIntercontinentalSuperCup: "Mannertenvälinen cup",
  compTypeClubFriendlyDomestic: "Kansalliset seurojen harjoitusottelut",
  compTypeClubFriendlyInternational: "Kansainväliset seurojen harjoitusottelut",
  compTypeNationalTeamFriendly: "Maajoukkueiden harjoitusottelut",
  confedAfc: "Aasia",
  confedCaf: "Afrikka",
  confedConcacaf: "Pohjois- ja Keski-Amerikka",
  confedConmebol: "Etelä-Amerikka",
  confedFifa: "Maailma",
  confedOfc: "Oseania",
  confedUefa: "Eurooppa",
  seoCompetitionsTitle: "Kaikki jalkapallokilpailut",
  seoCompetitionsDesc: "Jokainen sarja, cup ja kansainvälinen kilpailu, jota seuraamme, ryhmiteltynä tyypin ja alueen mukaan.",
  seoTeamsTitle: "Kaikki jalkapallojoukkueet",
  seoTeamsDesc: "Kaikki seuraamamme seurat ja maajoukkueet: kunkin alueen parhaat joukkueet, seurat maittain ja maajoukkueet alueittain.",
  teamsTopClubs: "Huippuseurat",
  teamsTopNational: "Parhaat maajoukkueet",
  teamsClubsByCountry: "Seurat maittain",
  teamsNationalByRegion: "Maajoukkueet alueittain",
  teamsOtherClubs: "Muut seurat",
  teamsCountOne: "{n} joukkue",
  teamsCount: "{n} joukkuetta",
  seoCompetitionTitle: "{competition}: yleiskatsaus",
  seoCompetitionDesc: "Yleiskatsaussivu kilpailulle {competition}.",
  seoCompetitionFixturesTitle: "{competition}: otteluohjelma {season}",
  seoCompetitionFixturesDesc: "Kilpailun {competition} {season} kaikki kierrokset: tähänastiset tulokset ja tulevat ottelut, kierros kerrallaan.",
  seoMatchesTitle: "Jalkapallo tänään: kaikki ottelut, {date}",
  seoMatchDayTitle: "Jalkapallo {date}: kaikki ottelut",
  seoMatchesDesc: "Kaikki jalkapallo-ottelut {date}, {n} kilpailusta: ennen ottelua alkamisaika, sen jälkeen tulos.",
  dayPickerAria: "Valitse päivä",
  seoCompetitionStatsTitle: "{competition}: tilastot {season}",
  seoCompetitionStatsDesc: "Kilpailun {competition} {season} parhaat joukkueet ja pelaajat jokaisessa tilastossa: maalit, {sotName}, syötöt, kaksinkamppailut, puolustus, kurinpito ja maalivahtipeli.",
  seoPlayerTitle: "{player} ({club}): yleiskatsaus",
  seoPlayerDesc: "Yleiskatsaussivu pelaajalle {player}, joukkue {club}.",
  filterAll: "Kaikki",
  filterClubs: "Seurat",
  filterNational: "Maajoukkueet",
  filterByType: "Suodata tyypin mukaan",
  filterByRegion: "Suodata alueen mukaan",
  filterAllTypes: "Kaikki tyypit",
  filterAllRegions: "Kaikki alueet",
  compTabsAria: "Kilpailun osiot",
  compTabOverview: "Yleiskatsaus",
  compTabMatchdays: "Kierrokset",
  compTabRounds: "Kierrokset",
  compTabRankings: "Rankingit",
  compSeason: "Kausi {season}",
  compColPos: "#",
  compColPlayed: "O",
  compColWins: "V",
  compColDraws: "T",
  compColLosses: "H",
  compColGoals: "Maalit",
  compColGoalDiff: "ME",
  compColPoints: "P",
  compSecTable: "Sarjataulukko",
  compSecSchedule: "Otteluohjelma",
  compPickerAria: "Valitse kierros",
  compNextTag: "Seuraava",
  compTBC: "Avoin",
  compTopMatch: "Huippuottelu",
  compSecDeserved: "Ansaittujen pisteiden taulukko",
  compDeservedExplainer: "{deservedName} ovat pisteet, jotka joukkueen {sotdName} yleensä tuo. {sotdNameStart} on joukkueen omat {sotName} miinus vastustajien {sotName}. Joukkue, jolla on vähemmän pisteitä kuin se ansaitsisi, on parempi kuin sarjataulukko kertoo; joukkue, jolla on enemmän, on huonompi.",
  compSecTeamRankings: "Joukkuerankingit",
  compSecPlayerRankings: "Pelaajarankingit",
  compTeamRankingsIntro: "Parhaat joukkueet {in} tällä kaudella, tilasto kerrallaan.",
  compPlayerRankingsIntro: "Parhaat pelaajat {in} tällä kaudella, tilasto kerrallaan.",
  compSecFacts: "Kausi numeroina",
  compFactGoalsPerMatch: "Maalia per ottelu",
  compFactGoalsInMatches: "{goals} maalia {matches} ottelussa",
  compFactHomeWins: "Kotivoitot",
  compFactOf: "{count} / {of}",
  compFactDrawsAway: "{draws} tasapeliä, {awayWins} vierasvoittoa",
  compFactBiggestMargin: "Suurin voitto",
  compFactMostGoals: "Eniten maaleja ottelussa",
  compFactLongestUnbeaten: "Pisin tappioton putki",
  compFactLongestWinless: "Pisin voitoton putki",
  compFactMatches: "{n} ottelua",
  compFactMatchday: "{n}. kierros",
  roundMatchweek: "{n}. kierros",
  roundWeek: "{n}. kierros",
  roundAperturaMatchday: "Apertura, {n}. kierros",
  roundClausuraMatchday: "Clausura, {n}. kierros",
  roundGroupStageMatchday: "Alkulohko, {n}. kierros",
  roundWcGroupMatchday: "Alkulohko, {n}. kierros",
  roundQualGroupMatchday: "Karsintalohko, {n}. kierros",
  roundOcSecondRoundMatchday: "2. karsintakierros, {n}. kierros",
  roundGroupMatchday: "{g}-lohko, {n}. kierros",
  roundLeaguePhaseMatchday: "Liigavaihe, {n}. kierros",
  roundLeagueStageMatchday: "Liigavaihe, {n}. kierros",
  roundNationsLeagueMatchday: "{g}-liiga, {n}. kierros",
  roundOf32: "32 parhaan kierros",
  roundWcOf32: "32 parhaan joukko",
  roundOf16: "Neljännesvälierät",
  roundOf: "{n} parhaan kierros",
  roundQuarterFinals: "Puolivälierät",
  roundQuarterfinalsAm: "Puolivälierät",
  roundSemiFinals: "Välierät",
  roundSemifinalsAm: "Välierät",
  roundPlayoffSemiFinals: "Jatkokarsinnan välierä",
  roundIpSemiFinal: "Välierä",
  roundOcThirdRoundSemiFinals: "Välierät",
  roundFinal: "Finaali",
  roundPlayoffFinal: "Jatkokarsinnan finaali",
  roundIpFinal: "Finaali",
  roundAsFifthRound: "5. karsintakierros",
  roundOcThirdRoundFinal: "Finaali",
  roundVlEuroFinal: "Eurokarsinnan finaali",
  roundThirdPlace: "Pronssiottelu",
  roundWcBronzeFinal: "Pronssiottelu",
  roundThirdPlaceMatch: "Pronssiottelu",
  roundQualifyingRound1: "1. karsintakierros",
  roundQualifyingRound2: "2. karsintakierros",
  roundQualifyingRound3: "3. karsintakierros",
  roundOcFirstRound: "1. karsintakierros",
  roundOcFirstRoundFinal: "1. karsintakierroksen finaali",
  roundPlayoffRound: "Playoff-kierros",
  roundKnockoutPlayoffs: "Pudotuspelivaiheen playoff",
  roundAfcPreliminaryStage: "Karsintakierros",
  roundPreliminaryRound1: "1. karsintakierros",
  roundPreliminaryRound2: "2. karsintakierros",
  roundLiberStage1: "1. karsintakierros",
  roundLiberStage2: "2. karsintakierros",
  roundLiberStage3: "3. karsintakierros",
  roundFirstRound: "1. kierros",
  roundSecondRound: "2. kierros",
  roundPreliminaryRound: "Esikarsinta",
  roundSeventhRound: "7. kierros",
  roundEighthRound: "8. kierros",
  roundFaQualifying1: "1. karsintakierros",
  roundFaQualifying2: "2. karsintakierros",
  roundFaQualifying3: "3. karsintakierros",
  roundFaQualifying4: "4. karsintakierros",
  roundFaQualifying1Replay: "1. karsintakierroksen uusintaottelu",
  roundFaQualifying2Replay: "2. karsintakierroksen uusintaottelu",
  roundFaQualifying3Replay: "3. karsintakierroksen uusintaottelu",
  roundFaQualifying4Replay: "4. karsintakierroksen uusintaottelu",
  roundFaFirstRoundProper: "1. kierros",
  roundQualFirstRound: "1. karsintakierros",
  roundAsSecondRoundGroupMatchday: "2. karsintakierros, {g}-lohko, {n}. kierros",
  roundAsThirdRoundMatchday: "3. karsintakierros, {n}. kierros",
  roundAsPlayoffsMatchday: "4. karsintakierros, {n}. kierros",
  roundCaFirstRound: "1. karsintakierros",
  roundCaSecondRoundMatchday: "2. karsintakierros, {n}. kierros",
  roundCaFinalRoundMatchday: "Finaalikierros, {n}. kierros",
  roundVlChampionshipMatchday: "Mestaruussarja, {n}. kierros",
  roundVlRelegationMatchday: "Karsintasarja, {n}. kierros",
  roundVlRelegationPlayoff: "Veikkausliigan karsinta",
  compVs: "vs",
  playedFullTime: "Päättynyt",
  playedAfterExtraTime: "Jatkoajan jälkeen",
  playedAfterPenalties: "Rangaistuspotkujen jälkeen",
  playedAwarded: "Tuomittu",
  awardNotPlayed: "Ottelua ei pelattu; tulos tuomittiin.",
  awardPlayed: "Pelattu {onPitch}; tulokseksi tuomittiin jälkikäteen {awarded}.",
  awardAbandoned: "Keskeytetty tilanteessa {onPitch}; tulokseksi tuomittiin {awarded}.",
  awardNotPlayedTo: "Ottelua ei pelattu; voitto tuomittiin joukkueelle {team}.",
  awardPlayedTo: "Pelattu {onPitch}; voitto tuomittiin jälkikäteen joukkueelle {team}.",
  awardAbandonedTo: "Keskeytetty tilanteessa {onPitch}; voitto tuomittiin joukkueelle {team}.",
  secGoals: "Maalit",
  goalPenalty: "Rangaistuspotku",
  goalOwnGoal: "Oma maali",
  goalAssist: "Syöttö: {name}",
  goalsNoMinutes: "Näiden maalien minuutteja ei ole kirjattu.",
  goalsNotRecorded: "Tämän kierroksen maalintekijöitä ei ole kirjattu.",
  secMatchLeaders: "Ottelun kärkipelaajat",
  leadersIntro: "Ottelun näkyvimmät pelaajat molemmista joukkueista.",
  leadersNotRecorded: "Pelaajien lukuja ei ole kirjattu tästä ottelusta.",
  leadersSideNotRecorded: "Joukkueen {team} pelaajien lukuja ei ole kirjattu tästä ottelusta.",
  secMatchStats: "Ottelutilastot",
  matchStatsIntro: "Kummankin joukkueen luvut tässä ottelussa.",
  matchStatsNotRecorded: "Joukkueiden lukuja ei ole kirjattu tästä ottelusta.",
  secLineups: "Kokoonpanot",
  lineupSubstitutes: "Vaihtopelaajat",
  lineupOff: "pois {minute}",
  lineupOn: "sisään {minute} pelaajan {player} tilalle",
  lineupMinutes: "minuuttia",
  lineupsNotRecorded: "Kokoonpanoja ei ole kirjattu tästä ottelusta.",
};

const STRINGS: Record<Lang, Dict> = { de: DE, en: EN, fi: FI };

/** Look up a chrome string; {placeholders} filled from `params`. Falls back to EN then the key. */
export function t(lang: Lang, key: string, params?: Record<string, string | number>): string {
  let s = STRINGS[lang]?.[key] ?? EN[key] ?? key;
  if (params) {
    for (const [k, v] of Object.entries(params)) s = s.replaceAll(`{${k}}`, String(v));
  }
  return s;
}

/** Competitions whose German name is masculine (its head noun is Cup or Pokal), so German reads
 *  "im {competition}"; every other competition reads "in der {competition}". */
const MASCULINE_IN_GERMAN = new Set(["DFBP", "FAC", "UESC", "WC", "CWC", "ACN", "AFCON", "GCUP", "CCCU"]);

/** "in {competition}" in the page's language, with the German article the competition's name takes. */
export function inCompetition(lang: Lang, leagueCode: string, name: string): string {
  return t(lang, MASCULINE_IN_GERMAN.has(leagueCode) ? "compInMasculine" : "compIn", { competition: name });
}

/** A played match's status word, from its served status and award: Awarded, After penalties,
 * After extra time or Full time. */
export function playedStatusWord(lang: Lang, status: string | null | undefined, awardKind: string | null | undefined): string {
  if (awardKind || status === "AWD" || status === "WO") return t(lang, "playedAwarded");
  if (status === "PEN") return t(lang, "playedAfterPenalties");
  if (status === "AET") return t(lang, "playedAfterExtraTime");
  return t(lang, "playedFullTime");
}

/** Spelled position from the payload `position_code` (F/M/D/G). Raw code shown for anything else. */
export function positionLabel(lang: Lang, code: string | null | undefined): string {
  const key = code ? `pos${code.toUpperCase()}` : "";
  const label = STRINGS[lang]?.[key] ?? EN[key];
  return label ?? (code ?? "");
}

/* ================================================================================================ *
 *  METRIC LABELS (#370) — the display name of a metric, per locale, in ONE place.
 *
 *  Before this, a metric's name lived in FOUR: the catalogue held `label_i18n_key` but no
 *  translation; `lib/metricRows.ts` hard-coded an English `label`; the three `heroSot*` keys above
 *  hard-coded three more; and `heroVerdict*` spells one out in prose. Nothing kept them in step, and
 *  the German and Finnish pages showed ENGLISH metric names because the catalogue's keys resolved to
 *  nothing at all.
 *
 *  KEYED BY THE CATALOGUE'S OWN `label_i18n_key`, verbatim, so the binding is explicit and a test can
 *  cross-check every key against `dbt_project/seeds/metric_catalogue.csv`. Division of ownership:
 *  the catalogue owns a metric's IDENTITY, direction and format; this file owns its DISPLAY STRING.
 *  Display copy does not belong in a warehouse seed, which is why the translations are here and not
 *  in the CSV.
 *
 *  A DEDICATED map, not dotted keys inside the Dicts above, and that is deliberate: a quoted dotted
 *  key is invisible to `scripts/check_copy_gate.py`'s entry regex AND to `check-page-specs.mjs`'s key
 *  extraction, so flat keys would have smuggled 54 strings past the copy check. This map has its own
 *  reader in the copy gate.
 *
 *  No name carries "Ø" or "%". A value averaged over several matches shows "per match" on a second
 *  line, and a share without a football word of its own shows "percentage" there: `metricSubline`
 *  below, from the keys in `SHARE_NAMED_BY_ITS_COUNT`.
 * ================================================================================================ */

type MetricLabels = Record<string, string>;

const METRIC_LABELS_EN: MetricLabels = {
  "metrics.goals_per_match.label": "Goals",
  "metrics.goals_against_per_match.label": "Goals against",
  "metrics.clean_sheets.label": "Clean sheets",
  "metrics.clean_sheets_pct.label": "Clean sheets",
  "metrics.shots_per_match.label": "Shots",
  "metrics.shots_inside_box_pct.label": "Shots inside box",
  "metrics.shots_on_target_per_match.label": "Shots on target",
  "metrics.shots_on_goal_against_per_match.label": "Shots on target against",
  "metrics.shots_on_goal_difference_per_match.label": "Shots on target difference",
  "metrics.finishing_efficiency_pct.label": "Goals per shot on target",
  "metrics.duels_per_match.label": "Duels",
  "metrics.duels_won_pct.label": "Duels won",
  "metrics.defensive_actions_per_match.label": "Defensive actions",
  "metrics.passes_per_match.label": "Passes",
  "metrics.passes_accuracy_pct.label": "Pass accuracy",
  "metrics.passes_key_per_match.label": "Key passes",
  "metrics.corners_per_match.label": "Corners",
  "metrics.corners_against_per_match.label": "Corners against",
  "metrics.saves_pct.label": "Saves",
  "metrics.shots_on_goal_pct.label": "Shooting accuracy",
  "metrics.shots_inside_box_per_match.label": "Shots inside box",
  "metrics.passes_accurate_per_match.label": "Accurate passes",
  "metrics.passes_share_pct.label": "Possession",
  "metrics.dribbles_attempts_per_match.label": "Dribbles attempted",
  "metrics.dribbles_success_per_match.label": "Dribbles completed",
  "metrics.dribbles_success_pct.label": "Dribbles completed",
  "metrics.duels_won_per_match.label": "Duels won",
  "metrics.tackles_per_match.label": "Tackles",
  "metrics.interceptions_per_match.label": "Interceptions",
  "metrics.blocks_per_match.label": "Blocks",
  "metrics.saves_per_match.label": "Saves",
  "metrics.free_kicks_per_match.label": "Free kicks",
  "metrics.fouls_per_match.label": "Fouls",
  "metrics.offsides_per_match.label": "Offsides",
  "metrics.cards_yellow.label": "Yellow cards",
  "metrics.cards_red.label": "Red cards",
  "metrics.points_won.label": "Points",
  "metrics.deserved_points.label": "Deserved points",
  "metrics.deserved_points_gap.label": "Difference from deserved points",
  // Player metrics use the catalogue's `playerMetrics.*` keys.
  "playerMetrics.scorerPoints.goals": "Goals",
  "playerMetrics.scorerPoints.assists": "Assists",
  "playerMetrics.passAccuracy.total": "Passes",
  "playerMetrics.keyPasses.label": "Key passes",
  "playerMetrics.shots.label": "Shots",
  "playerMetrics.shotsOnTarget.label": "Shots on target",
  "playerMetrics.finishingEfficiency.label": "Goals per shot on target",
  "playerMetrics.passAccuracy.label": "Pass accuracy",
  "playerMetrics.dribbles.attempts": "Dribbles attempted",
  "playerMetrics.minutesPerAppearance.label": "Minutes per appearance",
  "playerMetrics.duels.total": "Duels",
  "playerMetrics.duels.won": "Duels won",
  "playerMetrics.defensiveActions.label": "Defensive actions",
  "playerMetrics.fouls.label": "Fouls",
  "playerMetrics.cards.yellow": "Yellow cards",
  "playerMetrics.cards.red": "Red cards",
  "playerMetrics.savePct.saves": "Saves",
  // The metric GROUPS (#152): a group is defined by its key and order in the catalogue and by
  // these names, keyed `metricGroups.<metric_group>.label`. The key set is bound to
  // `src/data/metric_groups.json` by `check-metric-labels.test.mjs`.
  "metricGroups.goals.label": "Goals",
  "metricGroups.shooting.label": "Shooting",
  "metricGroups.passing.label": "Passing",
  "metricGroups.one_on_one.label": "One-on-one",
  "metricGroups.defending.label": "Defending",
  "metricGroups.discipline.label": "Discipline",
  "metricGroups.goalkeeping.label": "Goalkeeping",
  "metricGroups.set_pieces.label": "Set pieces",
  "metricGroups.outcomes.label": "Results",
  "metricGroups.playing_time.label": "Playing time",
};

const METRIC_LABELS_DE: MetricLabels = {
  "metrics.goals_per_match.label": "Tore",
  "metrics.goals_against_per_match.label": "Gegentore",
  "metrics.clean_sheets.label": "Zu-Null-Spiele",
  "metrics.clean_sheets_pct.label": "Zu-Null-Spiele",
  "metrics.shots_per_match.label": "Schüsse",
  "metrics.shots_inside_box_pct.label": "Schüsse aus dem Strafraum",
  // kicker and bundesliga.com use "Torschüsse" for all shots; a shot on target is "aufs Tor".
  "metrics.shots_on_target_per_match.label": "Schüsse aufs Tor",
  "metrics.shots_on_goal_against_per_match.label": "Zugelassene Schüsse aufs Tor",
  "metrics.shots_on_goal_difference_per_match.label": "Differenz der Schüsse aufs Tor",
  "metrics.finishing_efficiency_pct.label": "Trefferquote",
  "metrics.duels_per_match.label": "Zweikämpfe",
  "metrics.duels_won_pct.label": "Gewonnene Zweikämpfe",
  "metrics.defensive_actions_per_match.label": "Defensivaktionen",
  "metrics.passes_per_match.label": "Pässe",
  // bundesliga.com's word for the share; "Angekommene Pässe" is the count.
  "metrics.passes_accuracy_pct.label": "Passquote",
  // "Schlüsselpässe", not "Torschussvorlagen": the latter means shot assists, a different metric.
  "metrics.passes_key_per_match.label": "Schlüsselpässe",
  "metrics.corners_per_match.label": "Ecken",
  "metrics.corners_against_per_match.label": "Ecken gegen",
  "metrics.saves_pct.label": "Gehaltene Schüsse",
  "metrics.shots_on_goal_pct.label": "Schussgenauigkeit",
  "metrics.shots_inside_box_per_match.label": "Schüsse aus dem Strafraum",
  "metrics.passes_accurate_per_match.label": "Angekommene Pässe",
  "metrics.passes_share_pct.label": "Ballbesitz",
  "metrics.dribbles_attempts_per_match.label": "Dribblings",
  "metrics.dribbles_success_per_match.label": "Erfolgreiche Dribblings",
  "metrics.dribbles_success_pct.label": "Erfolgreiche Dribblings",
  "metrics.duels_won_per_match.label": "Gewonnene Zweikämpfe",
  "metrics.tackles_per_match.label": "Tacklings",
  "metrics.interceptions_per_match.label": "Abgefangene Pässe",
  "metrics.blocks_per_match.label": "Geblockte Bälle",
  "metrics.saves_per_match.label": "Gehaltene Schüsse",
  "metrics.free_kicks_per_match.label": "Freistöße",
  "metrics.fouls_per_match.label": "Fouls",
  "metrics.offsides_per_match.label": "Abseits",
  "metrics.cards_yellow.label": "Gelbe Karten",
  "metrics.cards_red.label": "Rote Karten",
  "metrics.points_won.label": "Punkte",
  "metrics.deserved_points.label": "Verdiente Punkte",
  "metrics.deserved_points_gap.label": "Differenz zu den verdienten Punkten",
  "playerMetrics.scorerPoints.goals": "Tore",
  "playerMetrics.scorerPoints.assists": "Torvorlagen",
  "playerMetrics.passAccuracy.total": "Pässe",
  "playerMetrics.keyPasses.label": "Schlüsselpässe",
  "playerMetrics.shots.label": "Schüsse",
  "playerMetrics.shotsOnTarget.label": "Schüsse aufs Tor",
  "playerMetrics.finishingEfficiency.label": "Trefferquote",
  "playerMetrics.passAccuracy.label": "Passquote",
  "playerMetrics.dribbles.attempts": "Dribblings",
  "playerMetrics.minutesPerAppearance.label": "Minuten pro Einsatz",
  "playerMetrics.duels.total": "Zweikämpfe",
  "playerMetrics.duels.won": "Gewonnene Zweikämpfe",
  "playerMetrics.defensiveActions.label": "Defensivaktionen",
  "playerMetrics.fouls.label": "Fouls",
  "playerMetrics.cards.yellow": "Gelbe Karten",
  "playerMetrics.cards.red": "Rote Karten",
  "playerMetrics.savePct.saves": "Gehaltene Schüsse",
  "metricGroups.goals.label": "Tore",
  "metricGroups.shooting.label": "Schüsse",
  "metricGroups.passing.label": "Pässe",
  "metricGroups.one_on_one.label": "Eins-gegen-eins",
  "metricGroups.defending.label": "Defensive",
  "metricGroups.discipline.label": "Disziplin",
  "metricGroups.goalkeeping.label": "Torwart",
  "metricGroups.set_pieces.label": "Standards",
  "metricGroups.outcomes.label": "Ergebnisse",
  "metricGroups.playing_time.label": "Einsatzzeit",
};

const METRIC_LABELS_FI: MetricLabels = {
  "metrics.goals_per_match.label": "Maalit",
  "metrics.goals_against_per_match.label": "Päästetyt maalit",
  "metrics.clean_sheets.label": "Nollapelit",
  "metrics.clean_sheets_pct.label": "Nollapelit",
  "metrics.shots_per_match.label": "Laukaukset",
  "metrics.shots_inside_box_pct.label": "Laukaukset boksista",
  "metrics.shots_on_target_per_match.label": "Laukaukset maalia kohti",
  "metrics.shots_on_goal_against_per_match.label": "Vastustajan laukaukset maalia kohti",
  "metrics.shots_on_goal_difference_per_match.label": "Laukausero maalia kohti",
  "metrics.finishing_efficiency_pct.label": "Viimeistelytehokkuus",
  "metrics.duels_per_match.label": "Kaksinkamppailut",
  "metrics.duels_won_pct.label": "Voitetut kaksinkamppailut",
  "metrics.defensive_actions_per_match.label": "Puolustustoimet",
  "metrics.passes_per_match.label": "Syötöt",
  "metrics.passes_accuracy_pct.label": "Syöttötarkkuus",
  "metrics.passes_key_per_match.label": "Avainsyötöt",
  "metrics.corners_per_match.label": "Kulmapotkut",
  "metrics.corners_against_per_match.label": "Päästetyt kulmapotkut",
  "metrics.saves_pct.label": "Torjuntaosuus",
  "metrics.shots_on_goal_pct.label": "Laukaustarkkuus",
  "metrics.shots_inside_box_per_match.label": "Laukaukset boksista",
  "metrics.passes_accurate_per_match.label": "Onnistuneet syötöt",
  "metrics.passes_share_pct.label": "Pallonhallinta",
  "metrics.dribbles_attempts_per_match.label": "Harhautukset",
  "metrics.dribbles_success_per_match.label": "Onnistuneet harhautukset",
  "metrics.dribbles_success_pct.label": "Onnistuneet harhautukset",
  "metrics.duels_won_per_match.label": "Voitetut kaksinkamppailut",
  "metrics.tackles_per_match.label": "Taklaukset",
  "metrics.interceptions_per_match.label": "Katkot",
  "metrics.blocks_per_match.label": "Blokit",
  "metrics.saves_per_match.label": "Torjunnat",
  "metrics.free_kicks_per_match.label": "Vapaapotkut",
  "metrics.fouls_per_match.label": "Rikkeet",
  "metrics.offsides_per_match.label": "Paitsiot",
  "metrics.cards_yellow.label": "Keltaiset kortit",
  "metrics.cards_red.label": "Punaiset kortit",
  "metrics.points_won.label": "Pisteet",
  "metrics.deserved_points.label": "Ansaitut pisteet",
  "metrics.deserved_points_gap.label": "Ero ansaittuihin pisteisiin",
  "playerMetrics.scorerPoints.goals": "Maalit",
  "playerMetrics.scorerPoints.assists": "Maalisyötöt",
  "playerMetrics.passAccuracy.total": "Syötöt",
  "playerMetrics.keyPasses.label": "Avainsyötöt",
  "playerMetrics.shots.label": "Laukaukset",
  "playerMetrics.shotsOnTarget.label": "Laukaukset maalia kohti",
  "playerMetrics.finishingEfficiency.label": "Viimeistelytehokkuus",
  "playerMetrics.passAccuracy.label": "Syöttötarkkuus",
  "playerMetrics.dribbles.attempts": "Harhautukset",
  "playerMetrics.minutesPerAppearance.label": "Minuuttia per ottelu",
  "playerMetrics.duels.total": "Kaksinkamppailut",
  "playerMetrics.duels.won": "Voitetut kaksinkamppailut",
  "playerMetrics.defensiveActions.label": "Puolustustoimet",
  "playerMetrics.fouls.label": "Rikkeet",
  "playerMetrics.cards.yellow": "Keltaiset kortit",
  "playerMetrics.cards.red": "Punaiset kortit",
  "playerMetrics.savePct.saves": "Torjunnat",
  "metricGroups.goals.label": "Maalit",
  "metricGroups.shooting.label": "Laukaukset",
  "metricGroups.passing.label": "Syötöt",
  "metricGroups.one_on_one.label": "Yksi vastaan yksi",
  "metricGroups.defending.label": "Puolustus",
  "metricGroups.discipline.label": "Kurinpito",
  "metricGroups.goalkeeping.label": "Maalivahti",
  "metricGroups.set_pieces.label": "Erikoistilanteet",
  "metricGroups.outcomes.label": "Tulokset",
  "metricGroups.playing_time.label": "Peliaika",
};

const METRIC_LABELS: Record<Lang, MetricLabels> = {
  de: METRIC_LABELS_DE,
  en: METRIC_LABELS_EN,
  fi: METRIC_LABELS_FI,
};

// Deliberately no `METRIC_LABEL_KEYS` / `METRIC_LABELS` export: the tests text-parse this file, as
// every other checker here does, so nothing imports them. Add an export when something actually does.

/**
 * Display name for a metric, by its catalogue `label_i18n_key`.
 *
 * Deliberately does NOT fall back to the key, unlike `t()` above. `t()` returns the key when a lookup
 * misses, which is tolerable for chrome (a developer sees it immediately) and unacceptable here: a
 * missing metric name would print `metrics.duels_per_match.label` on a public page for a reader.
 * Falls back to English, then to empty. `check-metric-labels.test.mjs` asserts every key resolves in
 * every locale, so neither fallback should ever be reachable in a shipped build.
 */
export function metricLabel(lang: Lang, labelKey: string): string {
  return METRIC_LABELS[lang]?.[labelKey] ?? METRIC_LABELS_EN[labelKey] ?? "";
}

/** A metric's name inside a sentence: a small first letter in English and Finnish; German nouns
 *  keep theirs. At the start of a sentence a string takes `metricLabel` as it is. */
export function metricInSentence(lang: Lang, labelKey: string): string {
  const label = metricLabel(lang, labelKey);
  return lang === "de" ? label : label.charAt(0).toLocaleLowerCase(lang) + label.slice(1);
}

// Shares without a football word of their own: each is named by its count, and "percentage" says
// it is the share. A share with its own word (Pass accuracy, Shooting accuracy) is not listed.
const SHARE_NAMED_BY_ITS_COUNT = new Set([
  "metrics.clean_sheets_pct.label",
  "metrics.shots_inside_box_pct.label",
  "metrics.duels_won_pct.label",
  "metrics.dribbles_success_pct.label",
  "metrics.saves_pct.label",
]);

/** A metric's second line: "per match" for a per-match value (the served fact, never read from an
 *  id), "percentage" for a share named by its count, otherwise empty. */
export function metricSubline(lang: Lang, labelKey: string, perMatch: boolean): string {
  if (perMatch) return t(lang, "perMatch");
  if (SHARE_NAMED_BY_ITS_COUNT.has(labelKey)) return t(lang, "percentage");
  return "";
}

/** A ranked board's TITLE on one line: the name, then its second line's words. */
export function boardTitle(lang: Lang, labelKey: string, perMatch: boolean): string {
  const label = metricLabel(lang, labelKey);
  const sub = metricSubline(lang, labelKey, perMatch);
  return label && sub ? `${label} ${sub}` : label;
}
