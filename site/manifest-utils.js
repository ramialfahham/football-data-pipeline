/**
 * Shared helpers for pages_export_manifest.json consumers.
 * Row counts drive routing (matchday vs recap); matchday_source_mart drives labeling.
 */
(function (global) {
  "use strict";

  /**
   * @param {string|null|undefined} sourceMart
   * @returns {'regular'|'relegation'|'unknown'}
   */
  function matchdaySourceKind(sourceMart) {
    const s = String(sourceMart || "").toLowerCase();
    if (!s) return "unknown";
    if (s.includes("relegation")) return "relegation";
    return "regular";
  }

  /**
   * @param {string} code league_code e.g. BL1
   * @param {string|null|undefined} sourceMart
   * @param {(key: string, fallback: string, vars?: object) => string} tt
   * @param {'landing'|'fixtureList'} [context='landing']
   */
  function competitionDisplayName(code, sourceMart, tt, context) {
    const upper = String(code || "").toUpperCase();
    const base = tt("competitions." + upper, upper);
    if (matchdaySourceKind(sourceMart) !== "relegation") {
      return base;
    }
    const suffixKey =
      context === "fixtureList"
        ? "fixtureList.context.relegationSuffix"
        : "landing.context.relegationSuffix";
    const suffix = tt(suffixKey, "Relegation");
    return `${base} · ${suffix}`;
  }

  /**
   * Find manifest entry for a domestic league code (case-insensitive).
   * @param {object|null} manifest
   * @param {string} code lower or upper league code
   */
  function manifestEntryForLeague(manifest, code) {
    const want = String(code || "").toUpperCase();
    const list = manifest && Array.isArray(manifest.domestic_leagues)
      ? manifest.domestic_leagues
      : [];
    return list.find((e) => String(e.league_code || "").toUpperCase() === want) || null;
  }

  global.MATCHDAYIQ_MANIFEST = {
    matchdaySourceKind,
    competitionDisplayName,
    manifestEntryForLeague,
  };
})(typeof window !== "undefined" ? window : globalThis);
