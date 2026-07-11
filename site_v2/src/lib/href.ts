// Base-aware internal links. Astro serves the site under `import.meta.env.BASE_URL`
// (this preview: "/v2/"); every internal href must carry that prefix so links keep
// working when the base changes at cutover (#377). Routing only — no identity/slug
// generation (slugs come from the payload / the registry-derived competitions map).

const BASE = import.meta.env.BASE_URL; // e.g. "/v2/", always ends with "/"

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
