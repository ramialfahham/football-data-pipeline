/*
 * Matchday IQ — i18n loader
 * =========================
 * Tiny shared loader for static-site translation. Each page references
 * this script via its appropriate relative path (e.g., "./i18n.js" from
 * the root, "../i18n.js" from a subpage). The loader detects its own
 * URL and resolves the i18n/<lang>.json file relative to itself.
 *
 * Usage in HTML:
 *   <element data-i18n="page.section.key">fallback text</element>
 *   <button data-i18n-attr="aria-label:nav.prev">…</button>
 *
 * Usage in JS:
 *   window.t("metric.tabellenplatz", "Tabellenplatz")  // sync read
 *   window.MATCHDAYIQ_I18N_READY.then((strings) => render(data))  // await load
 *
 * Switching:
 *   window.setLang("en")  // persists to localStorage, reloads page
 *
 * Adding a language: drop a new <code>.json in site/i18n/ and add the
 * code to SUPPORTED below.
 */
(function () {
  const SUPPORTED = ["de"];  // PR 2 adds "en"
  const FALLBACK = "de";

  // Resolve the i18n/ directory relative to this script's own URL so
  // each page (regardless of depth) loads the right JSON.
  const SCRIPT_URL = (document.currentScript && document.currentScript.src) || "";
  const I18N_BASE = SCRIPT_URL ? new URL("./i18n/", SCRIPT_URL).href : "./i18n/";

  function detectLang() {
    try {
      const stored = localStorage.getItem("matchdayiq.lang");
      if (stored && SUPPORTED.includes(stored)) return stored;
    } catch (e) { /* localStorage disabled */ }
    return FALLBACK;
  }

  function lookup(obj, key) {
    if (!obj || typeof key !== "string") return undefined;
    return key.split(".").reduce(
      (o, k) => (o && typeof o === "object") ? o[k] : undefined,
      obj
    );
  }

  function applyStaticStrings() {
    const strings = window.MATCHDAYIQ_I18N || {};
    document.documentElement.lang = window.MATCHDAYIQ_LANG;

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const v = lookup(strings, key);
      if (typeof v === "string") el.textContent = v;
    });

    document.querySelectorAll("[data-i18n-attr]").forEach((el) => {
      const spec = el.getAttribute("data-i18n-attr") || "";
      spec.split(",").forEach((pair) => {
        const parts = pair.split(":").map((s) => s && s.trim());
        if (parts.length !== 2) return;
        const [attr, key] = parts;
        const v = lookup(strings, key);
        if (typeof v === "string") el.setAttribute(attr, v);
      });
    });
  }

  // Public API
  window.MATCHDAYIQ_LANG = detectLang();
  window.MATCHDAYIQ_I18N = {};

  /** Look up a string by dotted key; returns fallback (or the key itself) when missing. */
  window.t = function (key, fallback) {
    const v = lookup(window.MATCHDAYIQ_I18N, key);
    if (typeof v === "string") return v;
    return fallback !== undefined ? fallback : key;
  };

  /** Look up a string and substitute {{vars}}. */
  window.tFmt = function (key, vars, fallback) {
    let s = window.t(key, fallback);
    if (vars && typeof s === "string") {
      Object.keys(vars).forEach((k) => {
        s = s.replace(new RegExp("\\{\\{\\s*" + k + "\\s*\\}\\}", "g"), String(vars[k]));
      });
    }
    return s;
  };

  /** Switch active language. Reloads the page so JSON refetches cleanly. */
  window.setLang = function (lang) {
    try {
      if (!SUPPORTED.includes(lang)) return;
      localStorage.setItem("matchdayiq.lang", lang);
      window.location.reload();
    } catch (e) { /* localStorage disabled */ }
  };

  /** Promise resolves to the loaded strings (or {} on failure). Pages that
   *  render dynamic content via JS should await this before reading t(). */
  window.MATCHDAYIQ_I18N_READY = fetch(I18N_BASE + window.MATCHDAYIQ_LANG + ".json")
    .then((r) => r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status)))
    .then((strings) => {
      window.MATCHDAYIQ_I18N = strings;
      // Replace text in elements that are already in the DOM at load time.
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", applyStaticStrings, { once: true });
      } else {
        applyStaticStrings();
      }
      return strings;
    })
    .catch((err) => {
      console.warn("[i18n] failed to load", window.MATCHDAYIQ_LANG, err);
      // Inline German fallback stays — no harm done.
      return {};
    });
})();
