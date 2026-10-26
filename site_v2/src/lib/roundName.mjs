// A round's name in the page's language, from what the warehouse serves (int_round_names): the
// copy key that names the round the way its competition does, and the number and group letter
// that name shows ("6. Spieltag", "A-lohko, 3. kierros"). The page never reads the provider's
// round text.
//
// Plain JS so `roundName.test.mjs` imports it under bare `node --test`; the caller passes `t`.

/** The name, or null when no key is served. */
export function roundName(t, lang, key, number, letter) {
  if (!key) return null;
  return t(lang, key, { n: number ?? "", g: letter ?? "" });
}
