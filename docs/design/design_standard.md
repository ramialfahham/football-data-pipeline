# Design standard

The site is simple and consistent: every part exists once, and pages only assemble parts.

## Who decides

- Visual details are decided by the coordinating agent against this standard. They are sizes, spacing, alignment, corners, separators, and which existing form of a part a page uses.
- The CPO decides what a fan sees and learns (data and blocks), wording, new features and cost. The CPO reviews each page group when it is done and can veto any page.

## Rules

1. Simplicity without a redesign. Approved pages keep their blocks, order and wording. A choice between forms is always one of the forms the site already has.
2. One form per part. A part looks the same on every page. Clubs and national teams use one template.
3. Fixed values only, held in `docs/design/components.yml`. Text sizes: 11, 13, 15, 18 and 20 px, and 30 px for big numbers. Weights: 400 and 700. Corners: 4 px on small marks, 8 px on boxes. Spacing: 2, 4, 8, 12, 16, 24, 36 and 48 px.
4. No separator dot. Facts are unbreakable units with a 12 px gap that wrap whole. A name and its qualifier form a two-line row. Inside wording, a comma.
5. Phone first: every page is judged at 375 px, then wide.
6. When this standard does not settle a case, follow how FotMob solves it, built from our existing parts.
7. Reuse before inventing: no new size, colour, element or look.

## Before the CPO sees a page

- It is the real site, or a mock that passes `design-mocks/check_mock_css.py`.
- A designer review runs at 375 px and 1280 px in EN, DE and FI. It finds the same kind of thing in the same form everywhere, a clear hierarchy, shared edges and an even rhythm. It finds no split unit, orphan word or needlessly tall row.
