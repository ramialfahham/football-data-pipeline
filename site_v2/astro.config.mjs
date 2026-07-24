// Matchday IQ v2 — Astro config.
// Contract: docs/site_architecture.md (epic #361).
// Static output only (Firebase Hosting, no SSR). All locales are URL-prefixed
// (/de/…, /en/…); the root performs a browser-language redirect with `en`
// fallback (§3 of the architecture doc — CPO-overridable default).
// `base` is "/" (site root). It was "/v2/" only for the earlier GitHub Pages
// subpath layout; the deploy target is now Firebase Hosting at the domain root,
// so the site serves from "/".
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://ramialfahham.github.io",
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
