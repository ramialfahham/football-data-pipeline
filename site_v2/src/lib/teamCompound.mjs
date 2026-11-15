const NO_BREAK_SPACE = String.fromCodePoint(0x00a0);
const NON_BREAKING_HYPHEN = String.fromCodePoint(0x2011);

/** The team before Finnish "-pelaajaan": joined to a one-word name, kept with the last word of several. */
export function teamBeforeCompound(lang, team) {
  if (lang !== "fi") return team;
  return team.includes(" ") ? `${team}${NO_BREAK_SPACE}${NON_BREAKING_HYPHEN}` : `${team}-`;
}
