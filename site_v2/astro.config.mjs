// Matchday IQ v2 — Astro config.
// Contract: docs/site_architecture.md (epic #361).
// Static output only (GitHub Pages, no SSR). All locales are URL-prefixed
// (/de/…, /en/…); the root performs a browser-language redirect with `en`
// fallback (§3 of the architecture doc — CPO-overridable default).
// `base` is "/v2/" for the build-phase preview — the MVP owns the live URL until the
// parity cutover (#377), when this flips to root. Wiring the live Pages publish of this
// /v2/ artifact is a separate, deliberately-reviewed change (CPO ruling 2026-07-11).
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://ramialfahham.github.io",
  output: "static",
  base: "/v2/",
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
