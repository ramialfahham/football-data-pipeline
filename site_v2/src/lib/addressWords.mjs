// The address words: the part of a page address that follows the reader's language
// (docs/site_architecture.md "Address words"). `address_words.json` is the only place a word is
// spelled; the site, the build checks and scripts/check_design_inventory.py all read it.
//
// Plain JS for the same reason as competitionOrder.mjs: the build checks import it under bare
// `node --test`.

import WORDS from "../i18n/address_words.json" with { type: "json" };

export { WORDS };

const TOP_WORDS = ["competitions", "matches", "teams", "players"];
const TAB_WORDS = ["matches", "stats"];

/** The address word for `key` in `lang`. Throws on an unknown key or language, so a typo fails the
 *  build instead of emitting a broken link. */
export function word(lang, key) {
  const w = WORDS[key]?.[lang];
  if (!w) throw new Error(`no address word "${key}" for language "${lang}"`);
  return w;
}

/** The key whose word in `lang` is `segment`, among `keys`, or null. */
function keyOf(lang, segment, keys) {
  return keys.find((k) => WORDS[k][lang] === segment) ?? null;
}

/** The path after the locale (`"mannschaften/x/"`) as the language-neutral key path
 *  (`"teams/x/"`), or the reverse with `toLang`. Translation is by position: the first segment is a
 *  top word or a competition slug (rule 5 keeps the two apart); the second is a tab word only after
 *  a slug; everything else is a name and passes through. `*` is a name, so a glob translates too. */
export function translatePath(rest, fromLang, toLang) {
  const segs = rest.split("/");
  const swap = (i, keys) => {
    const key = keyOf(fromLang, segs[i], keys);
    if (key) segs[i] = WORDS[key][toLang];
    return key;
  };
  if (segs.length > 0 && segs[0] !== "" && !swap(0, TOP_WORDS) && segs.length > 1 && segs[1] !== "") {
    swap(1, TAB_WORDS);
  }
  return segs.join("/");
}

/** Every language the table names, in the table's order. */
export function wordLanguages() {
  return Object.keys(Object.values(WORDS)[0]);
}

/** Throws when a competition slug equals an address word in any language: both sit directly after
 *  the locale, so the two pages would claim one address (rule 5). */
export function assertNoClash(slugs) {
  const words = new Map();
  for (const [key, byLang] of Object.entries(WORDS)) {
    for (const [lang, w] of Object.entries(byLang)) words.set(w, `${key} (${lang})`);
  }
  const clashes = [...new Set(slugs)].filter((s) => words.has(s)).map((s) => `${s} = ${words.get(s)}`);
  if (clashes.length) {
    throw new Error(`competition slug equals an address word: ${clashes.join(", ")}`);
  }
}
