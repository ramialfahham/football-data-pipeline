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
  const SUPPORTED = ["de", "en", "fi"];
  const FALLBACK = "de";
  // Maps internal lang code → BCP-47 locale for Intl.NumberFormat / DateTimeFormat.
  // Add an entry here when adding a new language to SUPPORTED.
  const LOCALES = { de: "de-DE", en: "en-GB", fi: "fi-FI" };

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

    // Wire up the language-switcher dropdown if the page has one.
    if (typeof window.installLangSwitcher === "function") {
      window.installLangSwitcher();
    }
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

  /** Locale of the active language (BCP-47), for Intl formatters. */
  window.MATCHDAYIQ_LOCALE = LOCALES[window.MATCHDAYIQ_LANG] || LOCALES[FALLBACK];

  /** Locale-aware number formatter. Returns "-" for null/undefined/NaN. */
  window.fmtNum = function (x, decimals) {
    if (x === null || x === undefined) return "-";
    const n = Number(x);
    if (!Number.isFinite(n)) return "-";
    return new Intl.NumberFormat(window.MATCHDAYIQ_LOCALE, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(n);
  };

  /** Locale-aware percentage formatter — input is a 0..1 ratio. */
  window.fmtPct = function (x) {
    if (x === null || x === undefined) return "-";
    const n = Number(x);
    if (!Number.isFinite(n)) return "-";
    return window.fmtNum(n * 100, 0) + "%";
  };

  /**
   * Language options shown in the dropdown. Code is the BCP-47-ish key
   * used as data-lang. Label is the language's own self-name (kept
   * untranslated by convention). Options whose code is not in SUPPORTED
   * are hidden at install time so users can't click into a broken state;
   * they stay in the list so a new language can be enabled by dropping
   * a JSON file and updating SUPPORTED.
   */
  const LANG_OPTIONS = [
    { code: "de", label: "Deutsch" },
    { code: "en", label: "English" },
    { code: "es", label: "Español" },
    { code: "fr", label: "Français" },
    { code: "it", label: "Italiano" },
    { code: "nl", label: "Nederlands" },
    { code: "pt", label: "Português" },
    { code: "fi", label: "Suomi" },
    { code: "ar", label: "العربية" },
  ];

  /**
   * CSS for the dropdown menu. Injected once into the page so subpages
   * don't have to duplicate it. Uses CSS variables defined by each page
   * (--panel, --line, etc.) so it picks up the page's theme automatically.
   */
  const DROPDOWN_CSS = `
    .lang { position: relative; }
    .lang-btn { cursor: pointer; }
    .lang-btn .caret { display: inline-block; transition: transform 0.2s ease; }
    .lang.open .lang-btn .caret { transform: rotate(180deg); }
    .lang-menu {
      position: absolute;
      top: calc(100% + 6px);
      right: 0;
      min-width: 200px;
      background: var(--panel, var(--card-bg, #161b38));
      border: 1px solid var(--line, var(--border, rgba(255,255,255,0.07)));
      border-radius: 12px;
      padding: 6px;
      display: none;
      flex-direction: column;
      gap: 1px;
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45);
      z-index: 100;
    }
    .lang.open .lang-menu { display: flex; }
    .lang-option {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-radius: 8px;
      color: var(--muted, var(--text-secondary, #98a3c9));
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      background: transparent;
      border: 0;
      text-align: left;
      font-family: inherit;
    }
    .lang-option:hover { background: var(--panel-soft, var(--card-bg-hover, #1c2349)); color: var(--text, #f1f3fb); }
    .lang-option.active { color: var(--accent-bright, #93c5fd); font-weight: 600; }
    .lang-option .code-tag {
      font-size: 11px;
      color: var(--text-tertiary, #5c6792);
      letter-spacing: 0.05em;
      font-weight: 700;
    }
    .lang-option.active .code-tag { color: var(--accent-bright, #93c5fd); }
  `;

  function injectDropdownStyles() {
    if (document.getElementById("matchdayiq-lang-dropdown-css")) return;
    const style = document.createElement("style");
    style.id = "matchdayiq-lang-dropdown-css";
    style.textContent = DROPDOWN_CSS;
    document.head.appendChild(style);
  }

  function buildMenu(activeLang) {
    const menu = document.createElement("div");
    menu.className = "lang-menu";
    menu.setAttribute("role", "menu");
    LANG_OPTIONS.forEach(function (opt) {
      if (!SUPPORTED.includes(opt.code)) return;  // hide unsupported entirely
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "lang-option" + (opt.code === activeLang ? " active" : "");
      btn.setAttribute("role", "menuitem");
      btn.setAttribute("data-lang", opt.code);
      btn.innerHTML =
        '<span>' + opt.label + '</span><span class="code-tag">' + opt.code.toUpperCase() + '</span>';
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        window.setLang(opt.code);
      });
      menu.appendChild(btn);
    });
    return menu;
  }

  /**
   * Wire up a language-switcher dropdown on the current page.
   *
   * Expects each page to have:
   *   <div class="lang">
   *     <button class="lang-btn">...<span class="code">DE</span>...</button>
   *   </div>
   *
   * Injects (if not already present): the dropdown CSS, the .lang-menu
   * with options for every SUPPORTED language, and click handlers.
   * Hides unsupported options. Closes the menu on outside-click.
   */
  window.installLangSwitcher = function () {
    const root = document.querySelector(".lang");
    if (!root) return;
    injectDropdownStyles();

    const btn = root.querySelector(".lang-btn");
    const codeEl = btn && btn.querySelector(".code");
    if (codeEl) codeEl.textContent = window.MATCHDAYIQ_LANG.toUpperCase();

    // Build or update the dropdown menu.
    let menu = root.querySelector(".lang-menu");
    if (menu) menu.remove();
    menu = buildMenu(window.MATCHDAYIQ_LANG);
    root.appendChild(menu);

    if (btn && !btn.dataset.langWired) {
      btn.dataset.langWired = "1";
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        root.classList.toggle("open");
      });
    }

    // Close menu on outside click (install once per document).
    if (!document.body.dataset.langOutsideWired) {
      document.body.dataset.langOutsideWired = "1";
      document.addEventListener("click", function (ev) {
        if (!root.contains(ev.target)) root.classList.remove("open");
      });
    }
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
