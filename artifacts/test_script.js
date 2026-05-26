
    const FEEDBACK_ENDPOINT = "https://script.google.com/macros/s/REPLACE_WITH_DEPLOYMENT_ID/exec";
    const FEEDBACK_TOKEN = "";
    const TZ = "Europe/Berlin";

    function isFeedbackEndpointConfigured() {
      const u = String(FEEDBACK_ENDPOINT || "").trim();
      if (!u || /REPLACE_WITH|PLACEHOLDER|__YOUR_/i.test(u)) return false;
      const okHost =
        /^https:\/\/script\.google\.com\//i.test(u)
        || /^https:\/\/script\.googleusercontent\.com\//i.test(u);
      const okPath = /\/(exec|dev)(\?|#|$|\/)/i.test(u);
      return okHost && okPath;
    }

    // German fallback strings — used if i18n.js fails to load. Production
    // strings live in /i18n/<lang>.json under the "matchPreview" namespace.
    // Helpers below read from window.t() which prefers the JSON value and
    // falls back to these constants when the key is missing.
    const FALLBACK_FOOT_AVG_DESC = "Durchschnittswert pro Spiel im Formfenster";
    const FALLBACK_FOOT_PCT_DESC = "Quote über alle Formspiele kombiniert - Summe der Treffer / Summe der Versuche, kein Mittelwert der Einzelquoten";
    const FALLBACK_FOOT_MISSING_DESC = "Vom Datenanbieter nicht geliefert";
    const FALLBACK_FOOT_MISSING_WC_DESC = "Keine Qualifikationsdaten verfügbar. Gastgeberländer spielen keine Qualifikation und zeigen - bei allen Formkennzahlen vor Turnierbeginn.";
    const FALLBACK_FEEDBACK_THANKS = "Danke! Feedback wurde gesendet.";
    const FALLBACK_FEEDBACK_ERROR = "Feedback konnte nicht gesendet werden.";
    const FALLBACK_FEEDBACK_ERROR_PREFIX = "Feedback nicht gespeichert:";
    const FALLBACK_FEEDBACK_NOT_CONFIGURED = "Kein Feedback-Endpunkt in dieser Seite: Trage die Web-App-URL (…/exec) in site/match-preview/index.html ein ODER setze das GitHub-Actions-Geheimnis FEEDBACK_APPS_SCRIPT_URL und lasse „Deploy match preview“ neu laufen.";

    // Safe wrappers — work even if i18n.js hasn't defined window.t yet.
    function t(key, fallback) { return (window.t ? window.t(key, fallback) : fallback); }

    function nz(x) {
      const n = Number(x);
      return Number.isFinite(n) ? n : 0;
    }

    /** Locale-aware number formatter — delegates to window.fmtNum
     *  (defined by i18n.js). Falls back to DE comma-separator if i18n
     *  failed to load, so legacy behavior is preserved. */
    function fmtDe(x, decimals) {
      if (typeof window.fmtNum === "function") return window.fmtNum(x, decimals);
      if (x === null || x === undefined) return "-";
      const n = Number(x);
      if (!Number.isFinite(n)) return "-";
      return n.toFixed(decimals).replace(".", ",");
    }

    function fmtDePct(x) {
      if (typeof window.fmtPct === "function") return window.fmtPct(x);
      if (x === null || x === undefined) return "-";
      const n = Number(x);
      if (!Number.isFinite(n)) return "-";
      return `${fmtDe(n * 100, 0)}%`;
    }

    function berlinKickoff(iso) {
      // Locale comes from window.MATCHDAYIQ_LOCALE (set by i18n.js) so the
      // weekday name + 12/24h time formatting follows the active language.
      // Timezone stays Europe/Berlin since BL1 fixtures are scheduled there.
      const locale = window.MATCHDAYIQ_LOCALE || "de-DE";
      return new Intl.DateTimeFormat(locale, {
        timeZone: TZ,
        weekday: "long",
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(iso));
    }

    function seasonDisplayLabel(row) {
      const explicit = String(row && row.season_display_label ? row.season_display_label : "").trim();
      if (explicit) return explicit;
      const y = Number(row && row.season_api_year);
      if (Number.isFinite(y)) return `Saison ${y}/${y + 1}`;
      return "Saison";
    }

    function competitionDisplayLabel(row) {
      const explicit = String(row && row.competition_display_name ? row.competition_display_name : "").trim();
      if (explicit) return explicit;
      const league = String(row && row.league_name ? row.league_name : "").trim();
      return league || "Wettbewerb";
    }

    function kickoffDisplayLabel(row) {
      const explicit = String(row && row.kickoff_display_label ? row.kickoff_display_label : "").trim();
      if (explicit) return explicit;
      return `Anstoß ${berlinKickoff(row.kickoff_datetime)}`;
    }

    function normalizedStageLabel(row) {
      const explicit = String(row && row.stage_display_label ? row.stage_display_label : "").trim();
      if (explicit) return explicit;
      const round = String(row && row.round_name ? row.round_name : "").trim();
      if (!round) return "Runde";
      const regularSeasonRound = /regular\s*season/i.test(round) && /(\d+)/.test(round);
      if (regularSeasonRound) {
        const n = round.match(/(\d+)/);
        if (n && n[1]) return `${n[1]}. Spieltag`;
      }
      return round;
    }

    // Extract the group letter for WC group-stage fixtures from the standings
    // group description on the row. Returns "A".."L" when both sides agree,
    // else "".
    function wcGroupLetter(row) {
      if (!row || String(row.league_code || "").toUpperCase() !== "WC") return "";
      const home = String(row.home_standings_group_description || "").trim();
      const away = String(row.away_standings_group_description || "").trim();
      if (!home || home !== away) return "";
      const m = home.match(/^Group\s+([A-Z])$/i);
      return m ? m[1].toUpperCase() : "";
    }

    function matchContextLine(row) {
      const competition = competitionDisplayLabel(row);
      const season = seasonDisplayLabel(row);
      const compSeason = [competition, season].filter(Boolean).join(" · ");
      const stage = normalizedStageLabel(row);
      const substage = String(row && row.substage_display_label ? row.substage_display_label : "").trim();
      const kickoff = kickoffDisplayLabel(row);
      const groupLetter = wcGroupLetter(row);
      const groupLabel = groupLetter
        ? (typeof window.tFmt === "function"
            ? window.tFmt("matchPreview.wc.groupPrefix", "Group {{letter}}", { letter: groupLetter })
            : `Group ${groupLetter}`)
        : "";
      return [compSeason, stage, groupLabel, substage, kickoff].filter(Boolean).join(" · ");
    }

    function formContextLabel(row, leagueCode) {
      if (leagueCode === "wc") {
        const fromQualifiers = !!(row && row.home_form_from_qualifiers && row.away_form_from_qualifiers);
        if (fromQualifiers) {
          return t("matchPreview.formContextWcQualifiers", "Form: all qualifying matches");
        }
        return t("matchPreview.formContextWcTournament", "Form: all World Cup matches so far");
      }
      if (row && Number(row.form_season_api_year) !== Number(row.season_api_year)) {
        return t("matchPreview.formContextDomesticPreseason", "Form: full previous season");
      }
      return t("matchPreview.formContextDomestic", t("matchPreview.formContext", "Form: last 5 matches this season"));
    }

    function isWcQualifierPhase(rows) {
      return Array.isArray(rows) && rows.some(r => r.home_form_from_qualifiers || r.away_form_from_qualifiers);
    }

    function buildFootHtml(leagueCode, rows) {
      function item(sym, desc) {
        return '<div class="foot-item"><span class="foot-sym">' + sym + '</span><span class="foot-def">' + escHtml(desc) + '</span></div>';
      }
      const avgDesc = t("matchPreview.footAvgDesc", FALLBACK_FOOT_AVG_DESC);
      const pctDesc = t("matchPreview.footPctDesc", FALLBACK_FOOT_PCT_DESC);
      const missingDesc = (leagueCode === "wc" && isWcQualifierPhase(rows))
        ? t("matchPreview.footMissingWcDesc", FALLBACK_FOOT_MISSING_WC_DESC)
        : t("matchPreview.footMissingDesc", FALLBACK_FOOT_MISSING_DESC);
      return item("Ø", avgDesc) + item("%", pctDesc) + item("–", missingDesc);
    }

    function setCompetitionContext(rows) {
      const el = document.getElementById("competition-context");
      if (!el) return;
      const first = rows && rows.length ? rows[0] : {};
      const competition = competitionDisplayLabel(first);
      const season = seasonDisplayLabel(first);
      el.textContent = `${competition} - ${season}`;
    }

    function pointsDisplay(r, side) {
      const ptsRaw = side === "home" ? r.home_points_won_sum_form : r.away_points_won_sum_form;
      const gamesRaw = side === "home" ? r.home_form_games_played : r.away_form_games_played;
      const games = Number(gamesRaw);
      if (!Number.isFinite(games) || games === 0) return "-";
      if (ptsRaw === null || ptsRaw === undefined) return "-";
      const pts = Number(ptsRaw);
      if (!Number.isFinite(pts)) return "-";
      const maxPts = 3 * games;
      return `${pts}/${maxPts}`;
    }

    function rankLabel(v) {
      if (v === null || v === undefined || v === "") return "-";
      const n = Number(v);
      return Number.isFinite(n) ? String(n) : "-";
    }

    const LEGACY_METRIC_LABEL_KEYS = {
      league_rank: "metric.tabellenplatz",
      points_won_form: "metric.punkteausbeute",
      goals_per_match_recent: "metric.tore",
      goals_against_per_match_recent: "metric.gegentore",
      shots_per_match_recent: "metric.schuesse",
      shot_accuracy_recent: "metric.schuesseAufsTor",
      danger_zone_ratio_recent: "metric.schuesseAusStrafraum",
      finishing_efficiency_recent: "metric.trefferquote",
      passes_per_match_recent: "metric.paesse",
      pass_accuracy_recent: "metric.angekommenePaesse",
      corner_kicks_per_match_recent: "metric.ecken",
      corners_conceded_per_match_recent: "metric.eckenGegen",
      save_ratio_recent: "metric.gehalteneTorschuesse",
    };

    function metricLabel(metricId) {
      const legacy = LEGACY_METRIC_LABEL_KEYS[metricId];
      const fallback = legacy ? t(legacy, metricId) : metricId;
      return t(`metrics.${metricId}.label`, fallback);
    }

    function escHtml(s) {
      return String(s ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function metricTableRows(r, defs, manifest) {
      const pct = (v) => (v === null || v === undefined || isNaN(Number(v))) ? null : Number(v) * 100;
      const num = (v) => (v === null || v === undefined || isNaN(Number(v))) ? null : Number(v);
      const formatDisplay = (raw, format, side) => {
        if (format === "points_fraction") return pointsDisplay(r, side);
        if (format === "integer") return rankLabel(raw);
        if (format === "percent") return fmtDePct(raw);
        if (format === "decimal_0") return fmtDe(raw, 0);
        return fmtDe(raw, 1);
      };
      const compareNum = (raw, format, side) => {
        if (format === "points_fraction") {
          const pts = side === "home" ? r.home_points_won_sum_form : r.away_points_won_sum_form;
          return num(pts);
        }
        if (format === "percent") return pct(raw);
        return num(raw);
      };
      const list = (manifest && manifest.metrics) || [];
      return list.map(({ metric_id: metricId, band }) => {
        const def = (defs && defs[metricId]) || {};
        const homeRaw = def.home_column ? r[def.home_column] : null;
        const awayRaw = def.away_column ? r[def.away_column] : null;
        return {
          label: metricLabel(metricId),
          home: formatDisplay(homeRaw, def.format, "home"),
          away: formatDisplay(awayRaw, def.format, "away"),
          homeNum: compareNum(homeRaw, def.format, "home"),
          awayNum: compareNum(awayRaw, def.format, "away"),
          band: band || "a",
          lowerIsBetter: !!def.lower_is_better,
        };
      });
    }

    function teamNameLabel(v, missingLabel) {
      const label = String(v ?? "").trim();
      return label || missingLabel;
    }

    function renderMetrics(rows) {
      return `<div class="metrics">${rows.map(renderMetricRow).join("")}</div>`;
    }

    function renderMetricRow(m) {
      // Decide who's "winning" this metric — affects subtle color highlight.
      let homeWin = false, awayWin = false;
      const hHas = m.homeNum !== null && Number.isFinite(m.homeNum);
      const aHas = m.awayNum !== null && Number.isFinite(m.awayNum);
      if (hHas && aHas) {
        if (m.lowerIsBetter) {
          homeWin = m.homeNum < m.awayNum;
          awayWin = m.awayNum < m.homeNum;
        } else {
          homeWin = m.homeNum > m.awayNum;
          awayWin = m.awayNum > m.homeNum;
        }
      }
      const homeCls = "metric-value" + (homeWin ? " is-winning" : "");
      const awayCls = "metric-value" + (awayWin ? " is-winning" : "");
      const bandCls = "metric metric-band-" + (m.band || "a");
      return `
        <div class="${bandCls}">
          <div class="metric-label">${escHtml(m.label)}</div>
          <div class="metric-row">
            <div class="${homeCls}">${m.home}</div>
            <div class="${awayCls}">${m.away}</div>
          </div>
        </div>`;
    }

    // Kept as alias for any external code calling renderTable
    function renderTable(rows) { return renderMetrics(rows); }

    let activeFixtureId = null;

    // (setFeedbackCopy removed — feedback modal labels are now driven
    //  by data-i18n attributes on the modal elements directly.)

    function showToast(message, isError = false) {
      const toast = document.getElementById("feedback-toast");
      toast.textContent = message;
      toast.style.display = "block";
      toast.style.background = isError ? "#5b1f2a" : "#174e30";
      toast.style.borderColor = isError ? "#8e3244" : "#2a8152";
      const ms = isError && String(message).length > 120 ? 12000 : 3500;
      setTimeout(() => { toast.style.display = "none"; }, ms);
    }

    function openFeedbackModal() {
      document.getElementById("feedback-modal-backdrop").style.display = "flex";
      document.getElementById("feedback-modal-backdrop").setAttribute("aria-hidden", "false");
    }

    function closeFeedbackModal() {
      document.getElementById("feedback-modal-backdrop").style.display = "none";
      document.getElementById("feedback-modal-backdrop").setAttribute("aria-hidden", "true");
    }

    async function submitFeedback() {
      if (!isFeedbackEndpointConfigured()) {
        showToast(t("matchPreview.feedback.notConfigured", FALLBACK_FEEDBACK_NOT_CONFIGURED), true);
        return;
      }
      const ease = Number(document.getElementById("feedback-ease").value);
      const clarity = Number(document.getElementById("feedback-clarity").value);
      const comment = String(document.getElementById("feedback-comment").value || "").trim().slice(0, 500);
      const payload = {
        ease_score: ease,
        clarity_score: clarity,
        improvement_text: comment,
        language: (window.MATCHDAYIQ_LANG || "de"),
        fixture_id: activeFixtureId,
        app_version: "pages-match-preview",
        submitted_at: new Date().toISOString(),
        feedback_token: FEEDBACK_TOKEN,
      };
      try {
        const resp = await fetch(FEEDBACK_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "text/plain" },
          body: JSON.stringify(payload),
        });
        const body = await resp.json().catch(() => null);
        const appOk = !!(body && body.ok);
        if (!resp.ok) {
          showToast(`${t("matchPreview.feedback.error", FALLBACK_FEEDBACK_ERROR)} (HTTP ${resp.status})`, true);
          return;
        }
        if (!appOk) {
          const detail = body && body.error ? String(body.error) : "unknown_error";
          showToast(`${t("matchPreview.feedback.errorDetailPrefix", FALLBACK_FEEDBACK_ERROR_PREFIX)} ${detail}`, true);
          return;
        }
        closeFeedbackModal();
        document.getElementById("feedback-comment").value = "";
        showToast(t("matchPreview.feedback.thanks", FALLBACK_FEEDBACK_THANKS));
      } catch (err) {
        const hint = err && String(err.message || err).includes("fetch")
          ? " Netzwerk/CORS prüfen; Web-App auf „Jeder“?"
          : "";
        showToast(`${t("matchPreview.feedback.error", FALLBACK_FEEDBACK_ERROR)}${hint}`, true);
      }
    }

    function render(rows, defs, manifest, requestedFixtureId, leagueCode) {
      document.getElementById("foot-note").innerHTML = buildFootHtml(leagueCode, rows);

      const sorted = [...rows].sort((a, b) => {
        const ta = new Date(a.kickoff_datetime).getTime();
        const tb = new Date(b.kickoff_datetime).getTime();
        if (ta !== tb) return ta - tb;
        return nz(a.fixture_sk) - nz(b.fixture_sk);
      });
      setCompetitionContext(sorted);

      const carousel = document.getElementById("carousel");
      carousel.innerHTML = "";

      // If a specific fixture was requested via ?fixture=<id>, find its index
      // in the sorted list so we can scroll the carousel to it after render.
      // Coerce types defensively — fixture_api_id is numeric in the JSON,
      // but the URL param arrives as a string.
      const wantId = requestedFixtureId == null ? null : String(requestedFixtureId);
      let targetIndex = -1;
      if (wantId !== null) {
        targetIndex = sorted.findIndex((r) => String(r.fixture_api_id) === wantId);
      }
      // Seed activeFixtureId with the requested one (so feedback context tags
      // the right fixture even before the scroll handler fires).
      if (targetIndex >= 0) activeFixtureId = Number(sorted[targetIndex].fixture_api_id);

      sorted.forEach((row) => {
        if (activeFixtureId === null) activeFixtureId = row.fixture_api_id;
        const article = document.createElement("article");
        article.className = "card";
        article.dataset.fixtureId = row.fixture_api_id;
        const homeTeam = teamNameLabel(row.home_team_name, "DATA_ERROR_HOME_TEAM");
        const awayTeam = teamNameLabel(row.away_team_name, "DATA_ERROR_AWAY_TEAM");
        const homeLogoUrl = String(row && row.home_team_logo_url ? row.home_team_logo_url : "").trim();
        const awayLogoUrl = String(row && row.away_team_logo_url ? row.away_team_logo_url : "").trim();
        const formContext = formContextLabel(row, leagueCode);
        article.innerHTML = `
          <div class="preview-tag">${escHtml(t("matchPreview.tag", "Spielvorschau"))}</div>
          <div class="fixture">
            <div class="fixture-team fixture-home">
              <div class="team-logo-lg"><img src="${escHtml(homeLogoUrl)}" alt="${escHtml(homeTeam)}"></div>
              <div class="team-name-lg">${escHtml(homeTeam)}</div>
            </div>
            <div class="fixture-vs">vs</div>
            <div class="fixture-team fixture-away">
              <div class="team-logo-lg"><img src="${escHtml(awayLogoUrl)}" alt="${escHtml(awayTeam)}"></div>
              <div class="team-name-lg">${escHtml(awayTeam)}</div>
            </div>
          </div>
          <div class="kickoff">${escHtml(matchContextLine(row))}</div>
          <div class="form-context">${escHtml(formContext)}</div>
          ${renderMetrics(metricTableRows(row, defs, manifest))}
        `;
        carousel.appendChild(article);
      });

      carousel.addEventListener("scroll", () => {
        const w = carousel.clientWidth;
        const i = Math.round(carousel.scrollLeft / w);
        const cards = carousel.querySelectorAll(".card");
        const el = cards[i];
        if (el && el.dataset.fixtureId) activeFixtureId = Number(el.dataset.fixtureId);
      }, { passive: true });

      // Deep-link to the requested fixture by scrolling the carousel to its
      // card. Uses "auto" (instant) rather than "smooth" so users don't see
      // the first card flash before scroll — they land directly on the
      // fixture they clicked from the fixture list.
      if (targetIndex >= 0) {
        const cards = carousel.querySelectorAll(".card");
        const target = cards[targetIndex];
        if (target) {
          // Defer one frame so the carousel layout has settled and
          // scrollLeft has a meaningful target width to multiply against.
          requestAnimationFrame(() => {
            carousel.scrollTo({ left: target.offsetLeft, behavior: "auto" });
          });
        }
      }
    }

    function scrollByCard(dir) {
      const el = document.getElementById("carousel");
      el.scrollBy({ left: dir * el.clientWidth, behavior: "smooth" });
    }

    function start() {
      document.getElementById("prev-btn").addEventListener("click", () => scrollByCard(-1));
      document.getElementById("next-btn").addEventListener("click", () => scrollByCard(1));
      document.getElementById("feedback-open-btn").addEventListener("click", openFeedbackModal);
      const feedbackLink = document.getElementById("feedback-link");
      if (feedbackLink) {
        feedbackLink.addEventListener("click", (e) => {
          e.preventDefault();
          openFeedbackModal();
        });
      }
      document.getElementById("feedback-cancel-btn").addEventListener("click", closeFeedbackModal);
      document.getElementById("feedback-submit-btn").addEventListener("click", submitFeedback);
      document.getElementById("feedback-modal-backdrop").addEventListener("click", (ev) => {
        if (ev.target.id === "feedback-modal-backdrop") closeFeedbackModal();
      });

      // Resolve the matchday-insights URL: ?league=<code> → per-league export,
      // otherwise the legacy sibling (BL1 deep-link compat).
      const params = new URLSearchParams(window.location.search);
      const leagueParam = (params.get("league") || "").trim().toLowerCase();
      const validLeague = /^[a-z0-9]+$/.test(leagueParam) ? leagueParam : "";
      const feedbackParam = (params.get("feedback") || "").trim().toLowerCase();
      const shouldOpenFeedbackModal = feedbackParam === "1" || feedbackParam === "true" || feedbackParam === "open";
      const matchdayUrl = validLeague
        ? `../data/${validLeague}/matchday_insights.json`
        : "./matchday_insights.json";
      // Deep-link target: ?fixture=<api_id> scrolls the carousel to that
      // specific match. Validated to digits-only so we don't pass user
      // input into DOM queries.
      const fixtureParamRaw = (params.get("fixture") || "").trim();
      const requestedFixtureId = /^\d+$/.test(fixtureParamRaw) ? fixtureParamRaw : null;

      // Update back-link to preserve the ?league= param so users return to
      // the right fixture-list.
      const backLink = document.querySelector(".backbar .back");
      if (backLink && validLeague) {
        backLink.setAttribute("href", `../fixture-list/?league=${validLeague}`);
      }
      if (shouldOpenFeedbackModal) {
        requestAnimationFrame(openFeedbackModal);
      }

      // Wait for both i18n (translations) and the data fetch so the rendered
      // carousel uses translated labels on first paint.
      const i18nReady = window.MATCHDAYIQ_I18N_READY || Promise.resolve({});
      Promise.all([
        i18nReady,
        fetch(matchdayUrl).then((r) => r.json()),
        fetch("./metric_manifest.json").then((r) => r.json()),
        fetch("./metric_definitions.json").then((r) => r.json()),
      ])
        .then(([_, payload, manifest, defs]) => {
          render(payload.show || [], defs, manifest, requestedFixtureId, validLeague);
        })
        .catch((err) => {
          document.getElementById("carousel").innerHTML =
            `<article class="card">${escHtml(t("matchPreview.errorPrefix", "Daten konnten nicht geladen werden:"))} ${escHtml(String(err))}</article>`;
        });
    }

    // Deferred scripts (i18n.js) run after parsing but before DOMContentLoaded.
    // Wait for DCL so window.MATCHDAYIQ_I18N_READY is defined when start() runs.
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", start, { once: true });
    } else {
      start();
    }
  