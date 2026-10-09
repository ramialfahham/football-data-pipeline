// The menu's six items in the menu's order; the header, the phone drawer and the footer all read this
// list. An item carries an href only once its page is built; until then it renders as an inert span,
// styled the same as a link (09_chrome.md §6).
import { t } from "../i18n/strings";
import { localeHref, word } from "./href";
import type { Lang } from "./format";

export type Section = "competitions" | "matches" | "teams" | "players" | "standings" | "statistics";

export interface MenuItem {
  section: Section;
  label: string;
  href?: string;
}

export function menuItems(lang: Lang): MenuItem[] {
  return [
    { section: "competitions", label: t(lang, "navCompetitions"), href: localeHref(lang, `${word(lang, "competitions")}/`) },
    { section: "matches", label: t(lang, "navMatches"), href: localeHref(lang, `${word(lang, "matches")}/`) },
    { section: "teams", label: t(lang, "navTeams") },
    { section: "players", label: t(lang, "navPlayers") },
    { section: "standings", label: t(lang, "navStandings") },
    { section: "statistics", label: t(lang, "navStatistics") },
  ];
}
