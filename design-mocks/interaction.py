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
