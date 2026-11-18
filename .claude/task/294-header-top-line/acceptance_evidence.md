# Verification — the match header's top line

The measurements are in `rendered_page_evidence.md` in this folder: 18 match pages (cancelled,
abandoned, awaiting result, postponed, not started, played; EN, DE, FI) at 280, 320, 375 and 768px,
0 defects.

criteria_demonstrated:
  - **"Match preview" only while the match is still to be played; no top line on a cancelled, abandoned or awaiting-result page, its status in the kick-off line:** the not-started and postponed pages read "Match preview" / "Spielvorschau" / "Otteluennakko"; the cancelled, abandoned and awaiting-result pages have no `.mast .status-word`, and their kick-off line carries the status tag (Cancelled / Abgesagt / Peruttu, Abandoned / Abgebrochen / Keskeytetty, Awaiting result / Ergebnis ausstehend / Tulosta odotetaan); a played page keeps its status word. Same at every width from 280 to 768px, nothing clipped.
