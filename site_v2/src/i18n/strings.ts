// Fixture-page chrome strings (DE / EN / FI). The ~two dozen UI labels the fixture
// template needs. Metric ROW labels are the CPO-locked display strings in
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
  noRecentForm: "No recent matches",
  noMatchStats: "match stats not available",
  timeTBD: "time TBD",
  table: "Table",
  topScorers: "Top scorers",
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
  teamPlayed: "played",
  tabOverview: "Overview",
  tabPerformance: "Performance",
  tabSquad: "Squad",
  comingTitle: "Coming soon",
  comingPerformance: "Every metric ranked against the league and against last season. Landing with the next release.",
  comingSquad: "The full squad with per-player minutes and output. Landing with the next release.",
  // squad tab
  squadGk: "Goalkeepers", squadDef: "Defenders", squadMid: "Midfielders", squadFwd: "Forwards", squadOther: "Other",
  seasonToDate: "season to date",
  squadShown: "{shown} of {rostered} shown",
  squadEmpty: "No appearances recorded this season yet.",
  squadUnavailable: "Squad not available for this season.",
  appOne: "app", appMany: "apps", minsPerApp: "mins/app",
  goalOne: "goal", assistOne: "assist",
  vsLeague: "vs the league",
  vsLastSeason: "vs last season",
  median: "Median",
  rankedInLeague: "ranked within the league",
  vsPriorSeasonGames: "vs the same point last season ({n} games)",
  rankOfCount: "{rank} of {n}",
  unitPp: "pp",
  notRankable: "Not enough games this season to rank {team} against the league.",
  secDeserved: "Deserved vs actual",
  secYoY: "Vs last season",
  secFixtures: "Fixtures",
  // heroSotFor / heroSotAgainst / heroSotDiff removed (#370): they were a THIRD hand-written copy of
  // three metric names that the catalogue already identifies. The hero tiles now read them from
  // METRIC_LABELS below, like every other metric name on the site.
  heroVerdictUnder: "Play like {team}'s, a shots-on-target difference of {sotd} per match, usually earns about {deserved} points. They finished {gap} short of what they created.",
  heroVerdictOver: "Play like {team}'s, a shots-on-target difference of {sotd} per match, usually earns about {deserved} points. They took {gap} more than they created.",
  heroCaption: "Every dot is a {competition} team, placed by shots-on-target difference per match (left to right) against points won (up = more). The dashed line is the points that level of play usually earns.",
  heroNoData: "A deserved-vs-actual read needs a single league table, so it is shown for domestic leagues only.",
  axPoints: "Points won",
  axPlay: "Shots on target difference / match",
  trendLabel: "as expected",
  yoyPoints: "Points",
  yoyGoalsFor: "Goals",
  yoyGoalsAgainst: "Goals against",
  yoyThroughGames: "same point last season ({n} games)",
  noYoY: "No comparable season a year ago.",
  fxHome: "Home",
  fxAway: "Away",
  fxNext: "Next",
  linkFixtures: "Full fixture list",
  teamFootnote: "Sample data · v2 preview ({brand})",

  // SEO templates (#844). These are the ONLY reason a page's <title> and <meta description> differ
  // across locales: the entity name and the competition name are locale-independent (the registry
  // carries one `name` per competition), so the DESCRIPTIVE words carry the whole locale signal.
  // Before this, all three locales shipped byte-identical titles and descriptions.
  // Shape follows the approved wireframes verbatim -- 02_team_profile.md section 8 ends the team
  // title with the brand; 01_fixture_page.md section 8 ends the fixture title with the competition.
  // NO NUMBERS in these until #838 lands: `points` is a synthetic 3-1-0 tally computed regardless of
  // the competition's rules, so a templated "N points" would write a known-false figure into a
  // surface search engines cache independently of the page.
  // Colon, not an em dash. CPO 2026-07-28: the dash "looks terribly like AI generated" — and he is
  // right that it is a tell, especially as a clause separator. A colon is the conventional
  // entity-then-descriptor form in a page title, reads as edited rather than generated, and costs
  // two characters less against a budget these titles already overrun.
  // The middle is deliberately SHORT. It is byte-identical on all 3,250 team pages, so it
  // differentiates nothing between them, while the two parts that DO vary (the brand here, the
  // competition on the fixture title) are exactly what Google truncates first. Measured: the long
  // middle put the team title at 64 characters for "Manchester United" and 71 for "Borussia
  // Mönchengladbach", pushing the brand out of the result entirely. Spending the budget on a
  // constant and losing the variable is the wrong way round.
  // NO brand suffix. CPO reversed his earlier "keep the brand" ruling on 2026-07-28 after
  // seo-expert-reviewer argued it: a suffix is EARNED by equity, not a way to build it. It cost 17
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
  // this reason in this same PR and left English alone — treating it as the trusted baseline, which
  // is the failure this contract's own amendment 3 records. bi-analyst-reviewer caught it.
  seoTeamDesc: "{team} ({competition}): form, fixtures, squad and season statistics.",
  // NO descriptive middle on the fixture title. It carries TWO entity names plus a competition, so
  // any middle at all overruns: with "Form & Stats" the German came to 69 and the Finnish to 65.
  // Nothing is really lost — the query for a fixture page IS the two team names, "vs" already says
  // what kind of page this is, and the competition is the part that distinguishes a league meeting
  // from a cup tie. The keyword was costing the differentiator.
  // Shape matches seoTeamTitle above — `{entity}: <descriptor>`, no brand suffix — for the SAME
  // reason recorded there: the CPO removed the brand suffix on 2026-07-28 because a suffix is
  // earned by equity, and an identical one on every page reads as boilerplate.
  //
  // The competition is NOT in the title, and that is researched rather than preferred. Sofascore
  // ("SJK vs HJK live score, H2H and lineups | Sofascore") and FBref ("... Match Report - <date> |
  // FBref.com") both omit it; kicker uses an editorial headline with the teams only in the URL.
  // Keeping it failed 4 of 26 competitions against the 660px hard cap, worst 886px. It is not
  // lost: it stays in the breadcrumb, the URL and the JSON-LD superEvent.
  // Measured over every competition's worst real upcoming fixture: 597px, inside the 600px budget.
  //
  // ⚠ "Preview" is true only while a fixture page IS a preview. The export writes upcoming
  // fixtures only today (#861). When finished matches get pages this needs a played/upcoming
  // split, or every match report will be titled "Preview".
  seoFixtureTitle: "{home} vs {away}: Preview",
  // --- chrome (site-wide header/footer, #825) ---
  navCompetitions: "Competitions",
  navMatches: "Matches",
  navTeams: "Teams",
  navPlayers: "Players",
  navStandings: "Standings",
  navStats: "Stats",
  mainNavAria: "Main navigation",
  searchPlaceholder: "Search teams, players…",
  searchAria: "Search",
  themeToggleAria: "Toggle theme",
  menuAria: "Menu",
  footerAbout: "About",
  footerImprintPending: "Imprint (pending)",
  footerDataSource: "Data: API-Football",
  // --- landing (#367). PLACEHOLDER COPY: every string below is the CPO's (§10) and is drafted
  // here only so the page renders for his review. The DE/FI variants are literal translations of
  // the drafts, not authored copy — they are replaced in the same single copy pass.
  seoHomeTitle: "Football stats and match previews",
  seoHomeDesc: "Upcoming matches from every competition we cover.",
  homeNext: "Next matches",
  homeNoFixtures: "No matches scheduled right now.",
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
  confedAfc: "Asia",
  confedCaf: "Africa",
  confedConcacaf: "North & Central America",
  confedConmebol: "South America",
  confedFifa: "World",
  confedOfc: "Oceania",
  confedUefa: "Europe",
  seoCompetitionsTitle: "All football competitions",
  seoCompetitionsDesc: "Every league, cup and international competition we cover, grouped by type and region.",
  filterAll: "All",
  filterClubs: "Clubs",
  filterNational: "National teams",
  filterByType: "Filter by type",
  filterByRegion: "Filter by region",
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
  noRecentForm: "Keine aktuellen Spiele",
  noMatchStats: "Keine Spielstatistik",
  timeTBD: "Uhrzeit offen",
  table: "Tabelle",
  topScorers: "Torjäger",
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
  teamPlayed: "Spiele",
  tabOverview: "Übersicht",
  tabPerformance: "Leistung",
  tabSquad: "Kader",
  comingTitle: "Demnächst",
  // German keeps ONE sentence where EN and FI take two. The em dash here was a stylistic pause
  // between a subject and its only finite verb, not a clause break: splitting it leaves "Kommt
  // mit dem nächsten Release." — a finite verb with no subject, which German reads as an
  // imperative. EN "Landing…" and FI "Tulossa…" are non-finite fragments and split safely.
  // bi-analyst-reviewer FAIL, round 1; CPO ruling 2026-08-06.
  comingPerformance: "Jede Kennzahl im Vergleich zur Liga und zur Vorsaison kommt mit dem nächsten Release.",
  comingSquad: "Der komplette Kader mit Einsatzminuten und Scorerwerten je Spieler kommt mit dem nächsten Release.",
  // squad tab
  squadGk: "Torhüter", squadDef: "Abwehr", squadMid: "Mittelfeld", squadFwd: "Angriff", squadOther: "Sonstige",
  seasonToDate: "Saison bis dato",
  squadShown: "{shown} von {rostered} angezeigt",
  squadEmpty: "Noch keine Einsätze in dieser Saison erfasst.",
  squadUnavailable: "Kader für diese Saison nicht verfügbar.",
  appOne: "Einsatz", appMany: "Einsätze", minsPerApp: "Min./Einsatz",
  goalOne: "Tor", assistOne: "Vorlage",
  vsLeague: "vs. Liga",
  vsLastSeason: "vs. Vorsaison",
  median: "Median",
  rankedInLeague: "im Ligavergleich",
  vsPriorSeasonGames: "vs. gleicher Stand letzte Saison ({n} Spiele)",
  rankOfCount: "{rank} von {n}",
  unitPp: "pp",
  notRankable: "Zu wenige Spiele in dieser Saison, um {team} mit der Liga zu vergleichen.",
  secDeserved: "Verdient vs. tatsächlich",
  secYoY: "Vs. letzte Saison",
  secFixtures: "Spiele",
  // heroSot* removed (#370): the three German tile labels moved to METRIC_LABELS_DE unchanged.
  // ⚠ FOUR strings on the deserved-vs-actual block name this metric — the two sentences below, the
  // tile label in METRIC_LABELS_DE, the axis (`axPlay`) and the caption (`heroCaption`). Nothing binds
  // them, so revising one silently leaves three disagreeing. Change them together or not at all.
  // Wording is the CPO's (§10); `Torschussdifferenz` and `pro Spiel` are both his.
  heroVerdictUnder: "Ein Spiel wie das von {team}, eine Torschussdifferenz von {sotd} pro Spiel, bringt normalerweise etwa {deserved} Punkte. Sie blieben {gap} unter dem, was sie sich erspielt haben.",
  heroVerdictOver: "Ein Spiel wie das von {team}, eine Torschussdifferenz von {sotd} pro Spiel, bringt normalerweise etwa {deserved} Punkte. Sie holten {gap} mehr, als sie sich erspielt haben.",
  heroCaption: "Jeder Punkt ist eine {competition}-Mannschaft, eingeordnet nach der Torschussdifferenz pro Spiel (links nach rechts) gegen die geholten Punkte (oben = mehr). Die gestrichelte Linie ist der Punkteschnitt, den ein solches Spiel normalerweise bringt.",
  heroNoData: "Eine Verdient-vs.-tatsächlich-Einordnung braucht eine einzige Ligatabelle und wird daher nur für Ligen gezeigt.",
  axPoints: "Geholte Punkte",
  // Chrome, not a metric label: the `/ Spiel` suffix is axis grammar. See the ⚠ above heroVerdict*.
  axPlay: "Torschussdifferenz / Spiel",
  trendLabel: "wie erwartet",
  yoyPoints: "Punkte",
  yoyGoalsFor: "Tore",
  yoyGoalsAgainst: "Gegentore",
  yoyThroughGames: "gleicher Stand letzte Saison ({n} Spiele)",
  noYoY: "Keine vergleichbare Saison im Vorjahr.",
  fxHome: "Heim",
  fxAway: "Auswärts",
  fxNext: "Nächstes",
  linkFixtures: "Alle Spiele",
  teamFootnote: "Beispieldaten · v2-Vorschau ({brand})",

  // APPOSITIVE, not a preposition. The first version read "{team} in {competition}: …", justified as
  // avoiding the gender problem (die Bundesliga / der DFB-Pokal / die Premier League — a template
  // cannot inflect an article for a competition it does not know). That was a misdiagnosis: German
  // "in" before a named competition ALWAYS takes a case-marked article, so dropping it did not make
  // the sentence gender-neutral, it made it ungrammatical on every German team page. The
  // PARENTHETICAL form needs no article and no case, and all three locales now share it.
  // Parentheses in the description, not the en dash Gemini supplied: same anti-AI-tell reason, and
  // they sidestep the article problem too — "(Premier League)" needs no case-marked article, where
  // "in der/im {competition}" would need one the template cannot know.
  // "Kader" and "Spiele" are reused verbatim from the CPO-approved description below, so the two
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
  seoFixtureTitle: "{home} - {away}: Vorschau",
  // --- chrome (site-wide header/footer, #825) ---
  navCompetitions: "Wettbewerbe",
  navMatches: "Spiele",
  navTeams: "Mannschaften",
  navPlayers: "Spieler",
  navStandings: "Tabelle",
  navStats: "Statistiken",
  mainNavAria: "Hauptnavigation",
  searchPlaceholder: "Teams, Spieler suchen…",
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
  homeNoFixtures: "Derzeit sind keine Spiele angesetzt.",
  compTypeDomesticLeague: "Nationale Ligen",
  compTypeDomesticCup: "Nationale Pokale",
  compTypeContinentalCup: "Kontinentale Vereinspokale",
  compTypeContinentalSuperCup: "Kontinentale Superpokale",
  compTypeClubWorldCup: "Klub-Weltmeisterschaft",
  compTypeQualifying: "Nationalmannschafts-Qualifikation",
  compTypeContinentalChampionship: "Kontinentale Meisterschaften",
  compTypeWorldChampionship: "Weltmeisterschaft",
  confedAfc: "Asien",
  confedCaf: "Afrika",
  confedConcacaf: "Nord- und Mittelamerika",
  confedConmebol: "Südamerika",
  confedFifa: "Welt",
  confedOfc: "Ozeanien",
  confedUefa: "Europa",
  seoCompetitionsTitle: "Alle Fußballwettbewerbe",
  seoCompetitionsDesc: "Jede Liga, jeder Pokal und jeder internationale Wettbewerb, den wir abdecken, gruppiert nach Art und Region.",
  filterAll: "Alle",
  filterClubs: "Vereine",
  filterNational: "Nationalmannschaften",
  filterByType: "Nach Art filtern",
  filterByRegion: "Nach Region filtern",
};

const FI: Dict = {
  crumbHome: "Etusivu",
  crumbMatches: "Ottelut",
  eyebrowPreview: "Otteluennakko",
  // "kunto", not "muoto": muoto is shape/format, and the football sense of form is kunto —
  // corroborated by the MVP corpus, which renders "form window" as `kuntojakso`
  // (site/i18n/fi.json). CPO correction #867, extended to this key by CPO ruling 2026-08-06;
  // the deferral noted at seoTeamTitle below is now closed.
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
  noRecentForm: "Ei viimeaikaisia otteluita",
  noMatchStats: "Ei ottelutilastoja",
  timeTBD: "Aika auki",
  table: "Sarjataulukko",
  topScorers: "Maalintekijät",
  fullH2H: "Kaikki kohtaamiset",
  footnote: "Esimerkkidata · v2-esikatselu ({brand})",
  // "–" not "vs": the Finnish values were byte-identical to the English ones, so two of three
  // locales shipped the same <meta description>. Caught only after the cross-locale check was
  // tightened to fail on any GROUP of locales sharing a value rather than on all three matching —
  // the weaker form saw German differ and concluded the template was working.
  // "vs." to match this locale's own fixture TITLE. I had switched these to an en dash on the
  // unverified claim that Finnish football writing prefers one; the CPO's source uses "vs.", and
  // the page was contradicting itself — title "Palmeiras vs. Atletico-MG", description
  // "Palmeiras – Atletico-MG".
  // ⚠ RESIDUAL: this now differs from the EN string only by the full stop after "vs". The audit's
  // byte-identical check passes, but only just, and passing it is not the same as being localised.
  // A real Finnish description is copy, so it is the CPO's call, not a fix I can make quietly.
  aboutWithH2h: "{home} vs. {away} · {round}. Joukkueet ovat kohdanneet {meetings} kertaa: {record}.",
  aboutNoH2h: "{home} vs. {away} · {round}.",
  posF: "Hyökkäys", posM: "Keskikenttä", posD: "Puolustus", posG: "Maalivahti",
  // --- team page (Overview) ---
  crumbTeams: "Joukkueet",
  crumbAria: "Murupolku",
  tabsAria: "Joukkueen osiot",
  founded: "Perustettu",
  teamPlayed: "ottelua",
  tabOverview: "Yleiskatsaus",
  tabPerformance: "Suoritus",
  tabSquad: "Kokoonpano",
  comingTitle: "Tulossa",
  comingPerformance: "Jokainen tunnusluku sarjaan ja viime kauteen verrattuna. Tulossa seuraavassa julkaisussa.",
  comingSquad: "Koko kokoonpano pelaajakohtaisine peliminuutteineen ja tehopisteineen. Tulossa seuraavassa julkaisussa.",
  // squad tab
  squadGk: "Maalivahdit", squadDef: "Puolustajat", squadMid: "Keskikenttäpelaajat", squadFwd: "Hyökkääjät", squadOther: "Muut",
  seasonToDate: "kausi tähän mennessä",
  squadShown: "{shown}/{rostered} näytetään",
  squadEmpty: "Ei vielä otteluita tällä kaudella.",
  squadUnavailable: "Kokoonpanoa ei ole saatavilla tälle kaudelle.",
  appOne: "ottelu", appMany: "ottelua", minsPerApp: "min/ottelu",
  goalOne: "maali", assistOne: "syöttö",
  vsLeague: "vs. sarja",
  vsLastSeason: "vs. viime kausi",
  median: "Mediaani",
  rankedInLeague: "sarjavertailussa",
  vsPriorSeasonGames: "vs. sama kohta viime kaudella ({n} ottelua)",
  rankOfCount: "{rank}/{n}",
  unitPp: "pp",
  notRankable: "Liian vähän otteluita tällä kaudella, jotta {team} voisi verrata sarjaan.",
  secDeserved: "Ansaittu vs. toteutunut",
  secYoY: "Vs. viime kausi",
  secFixtures: "Ottelut",
  // heroSot* removed (#370): the three Finnish tile labels moved to METRIC_LABELS_FI.
  // ⚠ Same four-string trap as the German block above — these two sentences, the tile label, `axPlay`
  // and `heroCaption` all name this metric and nothing binds them. Change them together or not at all.
  // Wording is the CPO's (§10). `maalilaukauksien ero` is nominative here, as an appositive.
  heroVerdictUnder: "Tällainen peli, maalilaukauksien ero {sotd} ottelua kohden, tuottaa yleensä noin {deserved} pistettä. {team} jäi {gap} alle sen, minkä loi.",
  heroVerdictOver: "Tällainen peli, maalilaukauksien ero {sotd} ottelua kohden, tuottaa yleensä noin {deserved} pistettä. {team} sai {gap} enemmän kuin loi.",
  // ⚠ `eron` is a GENITIVE ending I inferred, not the CPO's word — his noun is `maalilaukauksien ero`.
  // The case is governed by the later `mukaan`. Finnish inflection is where #867 went wrong four times,
  // so this is unverified against a Finnish source; the CPO approved it knowing that.
  heroCaption: "Jokainen piste on {competition}-joukkue, sijoitettuna maalilaukauksien eron ottelua kohden (vasemmalta oikealle) ja kerättyjen pisteiden (ylös = enemmän) mukaan. Katkoviiva on pistemäärä, jonka tällainen peli yleensä tuottaa.",
  heroNoData: "Ansaittu vs. toteutunut -tarkastelu vaatii yhden sarjataulukon, joten se näytetään vain sarjoille.",
  axPoints: "Kerätyt pisteet",
  // Chrome, not a metric label: the `/ ottelu` suffix is axis grammar. See the ⚠ above heroVerdict*.
  axPlay: "Maalilaukauksien ero / ottelu",
  trendLabel: "odotetusti",
  yoyPoints: "Pisteet",
  yoyGoalsFor: "Maalit",
  yoyGoalsAgainst: "Päästetyt maalit",
  yoyThroughGames: "sama kohta viime kaudella ({n} ottelua)",
  noYoY: "Ei vertailukelpoista kautta vuotta aiemmin.",
  fxHome: "Koti",
  fxAway: "Vieras",
  fxNext: "Seuraava",
  linkFixtures: "Kaikki ottelut",
  teamFootnote: "Esimerkkidata · v2-esikatselu ({brand})",

  // Finnish takes an appositive rather than a genitive: a proper noun cannot be inflected from a
  // template, so "{team}: ..." (not "{team}n tilastot") is the only form that stays grammatical
  // for every club name.
  // CPO-supplied, 2026-07-28 (§10 — user-visible copy is his call). "kunto", not "muoto": muoto is
  // shape/format, and the football sense of form is kunto — corroborated by the MVP corpus, which
  // renders "form window" as `kuntojakso` (site/i18n/fi.json). `secForm` above carried the same
  // error; the CPO ruled on it 2026-08-06 and it is now `Kuntovertailu`, so that deferral is closed.
  // "ja" in the team title and "&" in the fixture title are both the CPO's own choices, kept as he
  // wrote them; only the length changed.
  seoTeamTitle: "{team}: tilastot, kunto, kokoonpano ja ottelut",
  // Was "{team} sarjassa {competition}: …". `sarjassa` is inessive and governs a case the bare
  // borrowed league name cannot carry ("Premier Leaguessa" / "Valioliigassa"), so the template read
  // as machine translation. Parentheses instead: no case, no inflection, and they work for a
  // league name in any language. Same form as the EN and DE descriptions.
  seoTeamDesc: "{team} ({competition}): kunto, ottelut, kokoonpano ja kauden tilastot.",
  // The capital K is the CPO's, verbatim. The previous note here said not to swap "vs." for an en
  // dash "without a Finnish source" — THE SOURCE NOW EXISTS: Yle and MTV Uutiset pair
  // Veikkausliiga teams as "KuPS–HJK", tight en dash, no spaces. That is also what gets FI under
  // the limit: "vs." overflowed by 1px on one competition (661 against a 660 hard cap), the tight
  // en dash lands at 634px. CPO approved 2026-08-03 with the source on the table.
  // Worst real fixture: 573px, the widest headroom of the three. See the EN entry for the reasoning.
  seoFixtureTitle: "{home}–{away}: Ennakko",
  // --- chrome (site-wide header/footer, #825) ---
  navCompetitions: "Kilpailut",
  navMatches: "Ottelut",
  navTeams: "Joukkueet",
  navPlayers: "Pelaajat",
  navStandings: "Sarjataulukko",
  navStats: "Tilastot",
  mainNavAria: "Päänavigaatio",
  searchPlaceholder: "Hae joukkueita, pelaajia…",
  searchAria: "Haku",
  themeToggleAria: "Vaihda teema",
  menuAria: "Valikko",
  footerAbout: "Tietoa",
  footerImprintPending: "Vastuutiedot (tulossa)",
  // `Tietolähde` is the validated corpus's own term for "data source" ("Tietolähde ei
  // toimittanut tätä arvoa", site/i18n/fi.json), so this is a real translation rather than the
  // English string left in place. CPO ruling 2026-08-06.
  footerDataSource: "Tietolähde: API-Football",
  // --- landing (#367). PLACEHOLDER, see the EN block.
  seoHomeTitle: "Jalkapallotilastot ja otteluennakot",
  seoHomeDesc: "Tulevat ottelut kaikista kattamistamme kilpailuista.",
  homeNext: "Seuraavat ottelut",
  homeNoFixtures: "Ei otteluita tällä hetkellä.",
  compTypeDomesticLeague: "Kansalliset sarjat",
  compTypeDomesticCup: "Kansalliset cupit",
  compTypeContinentalCup: "Mantereiden seuracupit",
  compTypeContinentalSuperCup: "Mantereiden supercupit",
  compTypeClubWorldCup: "Seurojen MM-kisat",
  compTypeQualifying: "Maajoukkueiden karsinnat",
  compTypeContinentalChampionship: "Mantereiden mestaruuskilpailut",
  compTypeWorldChampionship: "MM-kisat",
  confedAfc: "Aasia",
  confedCaf: "Afrikka",
  confedConcacaf: "Pohjois- ja Keski-Amerikka",
  confedConmebol: "Etelä-Amerikka",
  confedFifa: "Maailma",
  confedOfc: "Oseania",
  confedUefa: "Eurooppa",
  seoCompetitionsTitle: "Kaikki jalkapallokilpailut",
  seoCompetitionsDesc: "Jokainen sarja, cup ja kansainvälinen kilpailu, jota seuraamme, ryhmiteltynä tyypin ja alueen mukaan.",
  filterAll: "Kaikki",
  filterClubs: "Seurat",
  filterNational: "Maajoukkueet",
  filterByType: "Suodata tyypin mukaan",
  filterByRegion: "Suodata alueen mukaan",
};

const STRINGS: Record<Lang, Dict> = { de: DE, en: EN, fi: FI };

/** Look up a chrome string; {placeholders} filled from `params`. Falls back to EN then the key. */
export function t(lang: Lang, key: string, params?: Record<string, string | number>): string {
  let s = STRINGS[lang]?.[key] ?? EN[key] ?? key;
  if (params) {
    for (const [k, v] of Object.entries(params)) s = s.replace(`{${k}}`, String(v));
  }
  return s;
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
 *  ENGLISH IS UNCHANGED BY THIS TASK. Every EN string below is byte-identical to what shipped before,
 *  including `% Goals per shot on target`, which the CPO's MVP corpus calls `% Conversion rate` — two
 *  approved English names for one metric, a §10 pick left to him and recorded in the contract.
 *  DE/FI provenance: 10 are the CPO's validated MVP corpus (`site/i18n/*.json`), test-pinned so they
 *  cannot drift; the rest were written for this task and externally verified, EXCEPT the three
 *  Finnish forms the CPO supplied himself.
 * ================================================================================================ */

type MetricLabels = Record<string, string>;

const METRIC_LABELS_EN: MetricLabels = {
  "metrics.goals_per_match.label": "Ø Goals",
  "metrics.goals_against_per_match.label": "Ø Goals against",
  "metrics.clean_sheets.label": "Clean sheets",
  // The percent form of the row above, per the "% " prefix every percent metric here carries.
  // The fixture windows label the COUNT; the team page labels the SHARE (metricRows `team`).
  "metrics.clean_sheets_pct.label": "% Clean sheets",
  "metrics.shots_per_match.label": "Ø Shots",
  "metrics.danger_zone_ratio.label": "% Shots from box",
  "metrics.shots_on_target_per_match.label": "Ø Shots on target",
  "metrics.shots_on_goal_against_per_match.label": "Ø Shots on target against",
  "metrics.sot_difference_per_match.label": "Ø Shots on target difference",
  "metrics.finishing_efficiency.label": "% Goals per shot on target",
  "metrics.duels_per_match.label": "Ø Duels",
  "metrics.duels_won_pct.label": "% Duels won",
  "metrics.defensive_actions_per_match.label": "Ø Defensive actions",
  "metrics.passes_per_match.label": "Ø Passes",
  "metrics.pass_accuracy.label": "% Pass accuracy",
  "metrics.key_passes_per_match.label": "Ø Key passes",
  "metrics.corners_per_match.label": "Ø Corners",
  "metrics.corners_against_per_match.label": "Ø Corners against",
  "metrics.saves_pct.label": "% Save percentage",
};

const METRIC_LABELS_DE: MetricLabels = {
  "metrics.goals_per_match.label": "Ø Tore",
  "metrics.goals_against_per_match.label": "Ø Gegentore",
  // Statista and FootyStats DE both use "Zu-Null-Spiele"; Transfermarkt's "weiße Weste" is the other
  // live German idiom and was not chosen, because the statistical label is the one a stat row wants.
  "metrics.clean_sheets.label": "Zu-Null-Spiele",
  // The percent form of the row above. The "% " prefix carries the share, exactly as it does for
  // "% Trefferquote" and "% Gehaltene Torschüsse" below, so the noun itself needs no second word.
  "metrics.clean_sheets_pct.label": "% Zu-Null-Spiele",
  "metrics.shots_per_match.label": "Ø Schüsse",
  "metrics.danger_zone_ratio.label": "% Schüsse aus dem Strafraum",
  // CPO-SUPPLIED, 2026-07-31, verbatim: Torschüsse / Torschüsse gegen / Torschussdifferenz. This
  // replaces `Schüsse aufs Tor`, and it is the compact form Bundesliga, kicker and sport.de all use
  // as a stat label. It also makes the German internally consistent, since `saves_pct` already reads
  // `% Gehaltene Torschüsse`. The Ø prefix is retained: the underlying metrics are per-match, and
  // without it `Torschüsse` reads as a season total.
  // ⚠ He chose `Torschussdifferenz` after being shown, with measurements, that an 18-character
  // compound clips in the 71px hero tile at 375px exactly as the Finnish compounds do. That is a
  // knowing decision, not an oversight; the fix belongs in the design system, not in his copy.
  "metrics.shots_on_target_per_match.label": "Ø Torschüsse",
  "metrics.shots_on_goal_against_per_match.label": "Ø Torschüsse gegen",
  "metrics.sot_difference_per_match.label": "Ø Torschussdifferenz",
  "metrics.finishing_efficiency.label": "% Trefferquote",
  // NOT "Duelle". Every German football source uses Zweikampf/Zweikämpfe — bundesliga.com's own stat
  // category is literally "Gewonnene Zweikämpfe", and kicker and sport.de agree. `Duelle` was my
  // first draft and it reads as a translation rather than as football German.
  "metrics.duels_per_match.label": "Ø Zweikämpfe",
  "metrics.duels_won_pct.label": "% Gewonnene Zweikämpfe",
  // halbfeldflanke defines Defensivaktionen as exactly this metric: balls intercepted, tackles
  // completed, duels won. It is also the denominator in the German PPDA definition.
  "metrics.defensive_actions_per_match.label": "Ø Defensivaktionen",
  "metrics.passes_per_match.label": "Ø Pässe",
  "metrics.pass_accuracy.label": "% Angekommene Pässe",
  // "Schlüsselpässe", not "Torschussvorlagen": the latter means shot assists, a different metric.
  "metrics.key_passes_per_match.label": "Ø Schlüsselpässe",
  "metrics.corners_per_match.label": "Ø Ecken",
  "metrics.corners_against_per_match.label": "Ø Ecken gegen",
  "metrics.saves_pct.label": "% Gehaltene Torschüsse",
};

const METRIC_LABELS_FI: MetricLabels = {
  "metrics.goals_per_match.label": "Ø Maalit",
  "metrics.goals_against_per_match.label": "Ø Päästetyt maalit",
  // Confirmed in Finnish football media (apu.fi on Veikkausliiga goalkeepers).
  "metrics.clean_sheets.label": "Nollapelit",
  "metrics.clean_sheets_pct.label": "% Nollapelit",
  // The percent form of the row above. The "% " prefix carries the share, as it does for
  // "% Torjuntaosuus" below, so no separate "osuus" compound is needed.
  "metrics.shots_per_match.label": "Ø Laukaukset",
  "metrics.danger_zone_ratio.label": "% Laukaukset boksista",
  // These three are CPO-SUPPLIED, 2026-07-31, including `vastaan`, which keeps Finnish parallel to
  // the German `gegen`. He chose them after being shown that his validated corpus and the old hero
  // tiles used two different forms for the same metric. His first form for the third one was
  // `maalilaukaisujen ero` and he revised it himself — see the note above that entry. An earlier
  // version of this comment claimed he supplied `laukaisujen` "verbatim", six lines above the note
  // recording that he had moved off it; no string below has ever contained that stem.
  // Capitalisation after the Ø/% prefix is house style, matching every other entry.
  "metrics.shots_on_target_per_match.label": "Ø Maalilaukaukset",
  "metrics.shots_on_goal_against_per_match.label": "Ø Maalilaukaukset vastaan",
  // CPO revised this on 2026-07-31 from `maalilaukaisujen ero` to `maalilaukauksien ero`, which is the
  // genitive plural of `maalilaukaus` and so matches `maalilaukaukset` above; `laukaisujen` came off a
  // different stem (`laukaisu`) and was internally inconsistent.
  "metrics.sot_difference_per_match.label": "Ø Maalilaukauksien ero",
  "metrics.finishing_efficiency.label": "% Viimeistelytehokkuus",
  // Veikkausliiga's own reporting uses kaksinkamppailut, and reports duels won as a percentage.
  "metrics.duels_per_match.label": "Ø Kaksinkamppailut",
  "metrics.duels_won_pct.label": "% Voitetut kaksinkamppailut",
  // CPO-confirmed 2026-07-31. I could not verify this one against a Finnish source — Veikkausliiga's
  // stats pages serve a broken certificate chain — and said so before he confirmed it.
  "metrics.defensive_actions_per_match.label": "Ø Puolustustoimet",
  "metrics.passes_per_match.label": "Ø Syötöt",
  "metrics.pass_accuracy.label": "% Syöttötarkkuus",
  // CPO-confirmed 2026-07-31, same unverified caveat as Puolustustoimet.
  "metrics.key_passes_per_match.label": "Ø Avainsyötöt",
  "metrics.corners_per_match.label": "Ø Kulmapotkut",
  "metrics.corners_against_per_match.label": "Ø Päästetyt kulmapotkut",
  "metrics.saves_pct.label": "% Torjuntaosuus",
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
