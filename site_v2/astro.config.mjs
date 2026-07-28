// Matchday Pilot v2 — Astro config.
// Contract: docs/site_architecture.md (epic #361).
// Static output only (Firebase Hosting, no SSR). All locales are URL-prefixed
// (/de/…, /en/…); the root performs a browser-language redirect with `en`
// fallback (§3 of the architecture doc — CPO-overridable default).
// `base` is "/" (site root). It was "/v2/" only for the earlier GitHub Pages
// subpath layout; the deploy target is now Firebase Hosting at the domain root,
// so the site serves from "/".
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import seoAudit from "./integrations/seo-audit.mjs";
import { SITEMAP_EXCLUDE } from "./src/config/indexability.mjs";

export default defineConfig({
  // The production origin. Was `https://ramialfahham.github.io` — a host DELETED on 2026-07-21 when
  // the MVP was retired, so every absolute URL derived from it would have resolved nowhere. This is
  // now consumed for real: every canonical, hreflang and OG URL is built from it (#844).
  // `www` -> apex is an HTTP redirect configured when the custom domain is connected in Firebase
  // Hosting; it is NOT expressible in firebase.json, whose redirects match on path only.
  site: "https://matchdaypilot.com",
  output: "static",
  base: "/",
  trailingSlash: "always",
  i18n: {
    // Live locales today (mirrors site/i18n.js SUPPORTED). Scale-out: #370.
    locales: ["de", "en", "fi"],
    defaultLocale: "en",
    routing: {
      prefixDefaultLocale: true,
    },
  },
  // ORDER MATTERS. Astro runs integration hooks sequentially in this array's order, so the audit is
  // placed AFTER sitemap() — it inspects the sitemap the previous integration just wrote.
  //
  // The sitemap is GENERATED even while the site is `noindex`. Deferring it entirely would leave its
  // 50k-per-file splitting and the locale-reciprocal index logic with ZERO exercise until go-live —
  // the exact ships-silently-then-breaks-live failure this gate exists to prevent. Nothing links it
  // and robots.txt does not advertise it, so a noindex corpus is not being announced.
  integrations: [
    sitemap({ filter: (page) => !SITEMAP_EXCLUDE.some((re) => re.test(new URL(page).pathname)) }),
    seoAudit(),
  ],
});
