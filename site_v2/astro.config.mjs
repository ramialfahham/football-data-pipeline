// Matchday IQ v2 — Astro config.
// Contract: docs/site_architecture.md (epic #361).
// Static output only (GitHub Pages, no SSR). All locales are URL-prefixed
// (/de/…, /en/…); the root performs a browser-language redirect with `en`
// fallback (§3 of the architecture doc — CPO-overridable default).
// `base` is intentionally NOT set yet: it is decided by the deploy step
// (preview under /v2/ while the MVP owns the live URL; flipped at cutover #377).
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://ramialfahham.github.io",
  output: "static",
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
