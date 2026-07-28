// Matchday Pilot v2 — Astro config.
// Contract: docs/site_architecture.md (epic #361).
// Static output only (Firebase Hosting, no SSR). All locales are URL-prefixed
// (/de/…, /en/…); the root performs a browser-language redirect with `en`
// fallback (§3 of the architecture doc — CPO-overridable default).
// `base` is "/" (site root). It was "/v2/" only for the earlier GitHub Pages
// subpath layout; the deploy target is now Firebase Hosting at the domain root,
// so the site serves from "/".
import { defineConfig } from "astro/config";

export default defineConfig({
  // The production origin. Was `https://ramialfahham.github.io` — a host DELETED on 2026-07-21 when
  // the MVP was retired, so every absolute URL derived from it would have resolved nowhere. Nothing
  // consumes Astro.site yet (canonical, hreflang and the sitemap arrive in PR C2), so this corrects a
  // latent-wrong value before anything starts depending on it.
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
});
