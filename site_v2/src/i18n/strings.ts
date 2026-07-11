// Fixture-page chrome strings (DE / EN / FI). The ~two dozen UI labels the fixture
// template needs. Metric ROW labels are the CPO-locked display strings in
// lib/metricRows.ts (identical across locales for now); wiring per-locale metric
// labels from the catalogue i18n keys is a follow-up (#370). Fresh to site_v2 — the
// MVP's site/i18n/ is a separate surface. Translations are standard football-UI terms;
// native DE/FI review welcome (noted in the handover).

import type { Lang } from "../lib/format";

type Dict = Record<string, string>;

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
  footnote: "Sample data · v2 preview (Matchday IQ)",
  aboutWithH2h: "{home} vs {away} · {round}. The two clubs have met {meetings} times — {record}.",
  aboutNoH2h: "{home} vs {away} · {round}.",
  posF: "Forward", posM: "Midfield", posD: "Defence", posG: "Goalkeeper",
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
  footnote: "Beispieldaten · v2-Vorschau (Matchday IQ)",
  aboutWithH2h: "{home} gegen {away} · {round}. Die Klubs trafen bereits {meetings} Mal aufeinander — {record}.",
  aboutNoH2h: "{home} gegen {away} · {round}.",
  posF: "Angriff", posM: "Mittelfeld", posD: "Abwehr", posG: "Tor",
};

const FI: Dict = {
  crumbHome: "Etusivu",
  crumbMatches: "Ottelut",
  eyebrowPreview: "Otteluennakko",
  secForm: "Muotovertailu",
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
  footnote: "Esimerkkidata · v2-esikatselu (Matchday IQ)",
  aboutWithH2h: "{home} vs {away} · {round}. Joukkueet ovat kohdanneet {meetings} kertaa — {record}.",
  aboutNoH2h: "{home} vs {away} · {round}.",
  posF: "Hyökkäys", posM: "Keskikenttä", posD: "Puolustus", posG: "Maalivahti",
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
