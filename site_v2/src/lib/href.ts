// Base-aware internal links. Astro serves the site under `import.meta.env.BASE_URL`;
// every internal href must carry that prefix so links keep working if the base ever
// changes. Routing only — no identity/slug generation (slugs come from the payload /
// the registry-derived competitions map).
import type { Lang } from "./format";
import { translatePath } from "./addressWords.mjs";

export { word } from "./addressWords.mjs";

const BASE = import.meta.env.BASE_URL; // e.g. "/v2/", always ends with "/"

/** The live locales, as a RUNTIME value — `Lang` in lib/format.ts is a type and erases at build.
 *
 * hreflang needs to enumerate every locale of the current page, so something has to hold the list
 * at runtime. This is the locale-ROUTING module, so it lives here rather than becoming a fifth
 * copy. Must stay in lockstep with `astro.config.mjs`'s `i18n.locales`; consolidating the remaining
 * copies (each page's `getStaticPaths`) is a separate cleanup. */
export const LOCALES: Lang[] = ["de", "en", "fi"];

/** The locale a built pathname belongs to, or null when it carries no locale segment (`/`).
 *
 * Reads `Astro.url.pathname`, which already includes BASE, so BASE is stripped first. */
export function localeOf(pathname: string): Lang | null {
  const withoutBase = pathname.startsWith(BASE) ? pathname.slice(BASE.length) : pathname.replace(/^\//, "");
  const first = withoutBase.split("/")[0];
  return (LOCALES as string[]).includes(first) ? (first as Lang) : null;
}

/** Every locale's URL for the page at `pathname`, for hreflang. Swaps the locale segment and maps
 * each address word through the word table (`translatePath`), so every language gets the address
 * its own route emits. Returns an empty map for a pathname with no locale segment (the root
 * redirect stub). */
export function alternatePaths(pathname: string): Record<string, string> {
  const current = localeOf(pathname);
  if (!current) return {};
  const withoutBase = pathname.startsWith(BASE) ? pathname.slice(BASE.length) : pathname.replace(/^\//, "");
  const rest = withoutBase.split("/").slice(1).join("/");
  return Object.fromEntries(LOCALES.map((l) => [l, localeHref(l, translatePath(rest, current, l))]));
}

/** Join the deploy base with an app-absolute path ("/en/…" -> "/v2/en/…"). */
export function href(path: string): string {
  const clean = path.startsWith("/") ? path.slice(1) : path;
  return `${BASE}${clean}`;
}

/** A locale-prefixed app path, e.g. localeHref("en", "brasileirao/") -> "/v2/en/brasileirao/". */
export function localeHref(lang: string, path = ""): string {
  const clean = path.startsWith("/") ? path.slice(1) : path;
  return href(`${lang}/${clean}`);
}
