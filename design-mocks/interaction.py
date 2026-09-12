"""THE INTERACTION STANDARD — what is clickable, where the click boundary is, how it signals.

The direction: *"mouse-over hover and then underlined club names is so 90s ... we need a
consistent approach: standardized where to click, which elements redirect where, standardizing
the elements"*.

Measured before designing (`scan_clickables.py`): NINE clickable element types across four
surfaces, SIX different hover treatments, and the affordance pointing at the wrong element — the
whole match row is the link, but hover underlined the *club name*, and a row has two of those.

## The two principles

**1. CLICKABILITY IS VISIBLE AT REST. Hover only confirms it.**
   An affordance that exists only on hover does not exist on a phone, and that is most readers.
   Underline-on-hover fails this twice: you cannot discover the link without a mouse, and when
   you do, it points at a word rather than the row.

**2. THE THING THAT RESPONDS IS THE THING YOU CLICK.**
   A row target makes the ROW respond. A chip target makes the CHIP respond. Never the text
   inside something larger.

## The four target types, and their whole state table

| Target        | At rest                              | Hover            | Active (touch) | Focus |
|---------------|--------------------------------------|------------------|----------------|-------|
| Row           | list structure + separators          | background lift  | deeper lift    | outline |
| Chip / button | its own border                       | border + text    | deeper fill    | outline |
| Heading link  | a chevron, always present            | chevron + text   | —              | outline |
| Prose link    | a real underline, always present     | text colour      | —              | outline |

⚠ **The prose row is not an inconsistency.** In running text there is nothing structural to
signal a link, so colour alone is not enough — that is an accessibility floor, not a style
choice. Everywhere else the element's own shape does the signalling, so the underline is noise.

⚠ **Green is not available for any of this.** `--accent` is reserved for "better value" and
`--loss` for a Loss pill (system.css's colour contract). Every state below moves along the
neutral ramp — `--muted` → `--ink-2` → `--ink`, and `--page` → `--surface` → `--sunk` — which is
also why it works in both themes with no extra rules.

## Two rules that are not about looks

- **Never nest a link inside a link.** A row that is a link may not contain a team link. Browsers
  do not even parse it reliably, and the reader cannot tell which target they hit.
- **One element, one destination.** If a row leads to the fixture, nothing inside it leads
  elsewhere. That ambiguity is exactly what the old underline created.
"""

CHEVRON = ('<svg class="chev" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
           '<path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.2"'
           ' stroke-linecap="round" stroke-linejoin="round"/></svg>')

INTERACTION_CSS = """
/* ================================================================ *
 *  INTERACTION STANDARD — one place, every surface.                 *
 *  Clickability is visible AT REST; hover only confirms it.         *
 *  The thing that responds is the thing you click.                  *
 *  Colour moves along the NEUTRAL ramp only: --accent is reserved   *
 *  for "better value" and --loss for a Loss pill.                   *
 * ================================================================ */

/* ---- 1. ROW TARGET -------------------------------------------- *
 * The whole row is the link, so the whole row responds. The lift is
 * inset past the text so it reads as one object rather than a
 * highlighted line of type. No underline anywhere inside it. */
a.fxrow, a.brow, a.tm-row {
  border-radius: 9px;
  margin-inline: -12px; padding-inline: 12px;
  transition: background-color .12s ease;
}
/* ⚠ hover is gated: on a touch device `:hover` can stick after a tap and leave a row looking
   permanently selected. `:active` below is the touch feedback. */
@media (hover: hover) {
  a.fxrow:hover, a.brow:hover, a.tm-row:hover { background: var(--surface); }
}
a.fxrow:active, a.brow:active, a.tm-row:active { background: var(--sunk); }

/* ⚠ NO TEXT DECORATION INSIDE A ROW TARGET. This is the rule that replaces
   `a.fxrow:hover .nm { text-decoration: underline }` — it underlined ONE of the two club names
   in a row whose target is neither of them. */
a.fxrow .nm, a.brow .nm, a.tm-row .nm { text-decoration: none; }

/* ---- 2. CHIP / BUTTON TARGET ---------------------------------- *
 * Already carries its own border at rest, which is the affordance.
 * Hover raises it one rung; active fills it. */
@media (hover: hover) {
  a.linkchip:hover { border-color: var(--ink-2); color: var(--ink); }
}
a.linkchip:active { background: var(--sunk); border-color: var(--ink-2); color: var(--ink); }

/* ---- 3. HEADING LINK ------------------------------------------ *
 * A competition heading that leads somewhere carries a CHEVRON at rest.
 * That is the whole point: the reader knows it is a link before touching
 * it, which an underline-on-hover never told them. */
.chev {
  width: 15px; height: 15px; flex: 0 0 auto; color: var(--muted);
  transition: transform .12s ease, color .12s ease;
}
a:hover > .chev, a:hover .chev { color: var(--ink-2); }
@media (hover: hover) {
  a.cnm:hover .chev { transform: translateX(2px); }
}
/* the heading text itself only moves along the ramp — never underlined */
a.cnm .nm { text-decoration: none; }

/* ---- 4. PROSE LINK -------------------------------------------- *
 * The ONE place an underline stays: running text has no structure of its
 * own to signal with, and colour alone is not an accessible signal. */
/* ⚠ THE `.fx` PREFIX IS LOAD-BEARING. `system.css` has `.fx a { text-decoration: none }` at
   specificity (0,1,1); a bare `p a` is (0,0,2) and LOSES, so the underline silently never
   appeared. Measured, not assumed — the rendered link reported `text-decoration-line: none`. */
.fx .lede a, .fx .bnote a, .fx p a, .fx .sub a {
  text-decoration: underline; text-underline-offset: 2px;
  text-decoration-color: var(--div); color: var(--ink);
}
.fx .lede a:hover, .fx .bnote a:hover, .fx p a:hover, .fx .sub a:hover {
  text-decoration-color: var(--ink-2);
}

/* ---- 5. BREADCRUMB -------------------------------------------- *
 * A link and the current page must differ AT REST, not on hover. */
.crumb a { color: var(--ink-2); text-decoration: none; }
.crumb .here { color: var(--muted); }
@media (hover: hover) { .crumb a:hover { color: var(--ink); } }

/* ---- 6. FOCUS ------------------------------------------------- *
 * Keyboard focus is a SEPARATE signal from hover and survives every choice
 * above. system.css already outlines `.fx a:focus-visible`; these two give
 * the row and chip targets a radius that matches their own shape. */
.fx a.fxrow:focus-visible,
.fx a.brow:focus-visible,
.fx a.tm-row:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; border-radius: 9px; }

@media (prefers-reduced-motion: reduce) {
  a.fxrow, a.brow, a.tm-row, .chev { transition: none; }
}
"""
