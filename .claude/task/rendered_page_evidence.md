# Rendered-page evidence — feat/navigation-rules-competition-shell

Branch `feat/navigation-rules-competition-shell`, base `main 56278d5`.

⛔ **This file previously documented a DIFFERENT branch** (`chore/roll-forward-sample`, fixture-page
metric labels) and said nothing about this diff. `bi-analyst-reviewer` FAILed round 1 for it, and
was right: an artifact describing another change is the same as an absent one.

Read against the running dev server (`preview_start` name `v2`, `http://localhost:4321`) after
`npm run build` reported `audit-seo: 166 built page(s) checked. OK.` Every number below is measured
from the rendered page, not from the CSS source — the point of this artifact is that a code read
cannot settle whether an affordance actually renders.

## What changed on screen

`HeroFixtures.astro`: the competition group heading was a `<span>`; it is now an `<a class="cnm">`
carrying an `<svg class="chev">`. Plus a new page at `/{lang}/{competition}/`.

## Desktop (1280x720)

- **Three heading links, three chevrons.** DOM read:
  `[{href:"/en/coppa-italia/", text:"Coppa Italia"}, {href:"/en/dfb-pokal/", text:"DFB-Pokal"},
  {href:"/en/saudi-pro-league/", text:"Saudi Pro League"}]` — one per group, all three groups.
- **The chevron is decoration, not a second label**: every `svg.chev` carries `aria-hidden="true"`,
  and the link's accessible text is the competition name alone.
  ⚠ The accessibility-tree reader initially showed these as `link [ref_4]` with NO name, which
  looked like a defect. It is not — the DOM read above shows the text is there. Recorded because
  the tree output is misleading here and the next person will hit it.
- **Chevron visible AT REST**, computed on the rendered element:
  `{display:"block", visibility:"visible", opacity:"1", w:15, h:15}`. It is in the markup and
  painted without hover, which is the whole claim of the rule (a hover-only affordance does not
  exist on a phone).
- **Match rows unchanged**: 4 `a.fxrow` in `dist/en/index.html`, **0** containing a nested `<a>`.
  The heading link lives in the sibling `.gh`, never inside a row.
- **The competition page renders**: `/en/dfb-pokal/` shows breadcrumb `Home › Competitions ›
  DFB-Pokal`, `<h1>DFB-Pokal</h1>`, and no content blocks. That is the scaffold, intentionally.

## Mobile (375x812) — where the real defect was

⛔ **This pass found a defect the desktop pass could not, and the contract's `done_when` had
required it from the start.**

| | before the fix | after |
|---|---|---|
| heading link box | **100 x 21** | 100 x 33 |
| meets 24x24 minimum target (WCAG 2.5.8) | **no** | yes |
| match row height, for scale | 81 | 81 |

A 21px-tall tap target on a touch device, next to an 81px row, is a real usability problem and it
is invisible at desktop width. Fixed in `system.css` with `padding-block: 6px; margin-block: -6px`
on `a.cnm` — the margin cancels the padding, so the hit area grows and the text does not move.

Verified after the fix, at 375px:

- `horizontalOverflow: false` (`scrollWidth 375 === clientWidth 375`) — nothing pushes the layout wide.
- Screenshot compared before/after: headings sit in the same place, separators intact, no overlap
  with the rows despite the link box (33px) now exceeding its `.gh` container (29px).
- Chevron still `15x15` and visible; names not truncated at the narrow width.

## Keyboard focus — the state the tap-target fix moved

⛔ **`bi-analyst-reviewer` FAILed round 2 for omitting this, and the omission hid a real defect.**
Its reasoning: `.fx a:focus-visible` draws its ring from the BORDER-box, and the tap-target fix
moves exactly that edge — so the one state most mechanically tied to the changed geometry was the
one left unmeasured.

⛔ **AND ROUND 3 FAILED AGAIN ON MY WRITE-UP OF IT.** I put the post-fix numbers under a "Measured
with REAL keyboard focus" header when they were arithmetic — the measured box plus *assumed*
outline constants — and disclosed that only in a footnote below the table. That is the same
overclaim, made while certifying the fix for an overclaim, and it mattered: the round-2 defect
existed BECAUSE hand-derived geometry was wrong. Redone properly below.

How focus was obtained (it is fiddly, and worth recording): click a non-interactive spot in the
page, then Tab. Programmatic `.focus()` does NOT match `:focus-visible` — it reports the UA default
outline instead — and `focus({focusVisible: true})` did not either. After a reload, focus lands on
`<body>` and Tab does nothing until the page is clicked again.

**Every number below is read under a confirmed `a.matches(':focus-visible') === true`, with the
outline width and offset read from `getComputedStyle` rather than assumed** (both measured 2px):

| group | prev element | height | ring vs `.gh` divider | clearance above | collides |
|---|---|---|---|---|---|
| Coppa Italia (**first**) | `.sechead` | 33 | clears by **0.7** | **13** | no, either side |
| DFB-Pokal | `.fxgroup` | 33 | clears by 0.7 | 13 | no, either side |
| Saudi Pro League | `.fxgroup` | 33 | clears by 0.7 | 13 | no, either side |

Before the fix, on the same first group under the same real focus: ring bottom **168.2** against the
divider at **165.8** — crossing it by 2.3px, with 16px unused above. So the reviewer's round-2
derivation was correct and the fix is confirmed against a rendered ring, not a calculation.

⭐ **The round-3 concern about the first group specifically is NOT borne out, and it was right to
demand the measurement.** The reasoning was that `.fxgroup:first-of-type{margin-top:10px}`
collapsing against `.sechead{margin-bottom:14px}` leaves ~14px, against a 13px upward ring reach —
about 1px of spare. Measured, the first group has the same **13px** clearance as the others
(`ringTop 124.2` vs `.sechead` bottom `111.2`), because the reach is measured from the link's
border-box, not from the un-padded text position the derivation assumed. Recorded because the
derivation was reasonable and still wrong, which is the whole argument for measuring.

⭐ The 0.7px is not slack and not a tuned number: `padding-bottom: 3` + the ring's 4px reach
(`outline-width 2` + `outline-offset 2`) = 7px = `.gh`'s own `padding-bottom`. The ring lands on
the divider's inner edge; 0.7 is the sub-pixel border itself. Any change to `.gh`'s padding must
move this with it.

## What this does NOT show

- **No dark/light toggle pass.** The new rules use only `--muted`/`--ink-2`/`--ink`, which are
  redefined by the light token block, so no hard-coded colour can leak — but that is reasoning from
  the CSS, not a rendered check, and it is stated as such.
- **No hover state captured.** `@media (hover: hover)` cannot be exercised meaningfully in this
  pane, and the rule's own point is that the at-rest affordance is what matters.
- ⚠ **An earlier version of this file computed the post-fix focus geometry instead of measuring it**
  and presented it under a "measured" header. That is corrected: every focus number above is now
  read under a confirmed `:focus-visible`, on each of the three groups, with the outline constants
  taken from `getComputedStyle`. Nothing in the focus section is derived.
