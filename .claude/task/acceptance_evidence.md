# Acceptance evidence — closed set instead of a moving boundary

criteria_demonstrated:
  - A LIVE REFERENCE IS NOT FLAGGED. `_dead_refs("#33 and #114 and #115 are live")` → `[]`.
    **#115 is the collision that motivated this branch** — the context-cleanup issue the CPO asked
    for as his reference, filed the same day the boundary shipped. Pinned in
    `test_the_guard_can_actually_fire` and again in
    `test_the_headroom_before_a_collision_is_stated`.
  - A DEAD REFERENCE IS FLAGGED. `_dead_refs("the authority is #753")` → `[753]`;
    `_dead_refs("see #153 and #156")` → `[153, 156]`. Those are the two real cases: #753 is the
    player page's phantom design authority, #153/#156 were `CLAUDE.md`'s "Next" line.
  - THE CSS COLOUR IS NOT AN ISSUE NUMBER.
    ``_dead_refs("| Weaker side | `#475569` (slate-600) |")`` → `[]`.
  - MUTATION 1 — a dead ref returns to `CLAUDE.md`: appended "the authority is #753" →
    `assert not {'CLAUDE.md': [753]}`, 1 failed, 2 passed. Restored → green.
  - ⛔ MUTATION 2 WAS CHERRY-PICKED THE FIRST TIME AND PROVED ALMOST NOTHING. I deleted `151` —
    which is the one member `min(DEAD_GITHUB_ISSUES) == 151` pins — and presented the red test as
    proof that removing a set member is caught. `platform-reviewer` showed the general claim was
    false: the three tests pinned exactly `{151, 153, 156, 753}`, so **4 of 256 members**, and
    deleting any of the other 252 left everything green. A mutation chosen from the covered set
    demonstrates nothing about the property it is offered for.
    FIXED with a sha256 digest over all 256 members, which catches deletion, addition AND
    substitution where a length check would miss the last. RE-RUN WITH A REPRESENTATIVE MUTATION:
    deleted `600` — a middle member, pinned by nothing —
    → `test_no_member_of_the_dead_set_can_be_removed_quietly` failed. Restored → 4 passed.
  - A SECOND FALSE-POSITIVE CLASS, also found by review rather than by me: `&#153;` is an HTML
    numeric character entity and matched as issue 153, which is IN the dead set. Neither guarded
    file contains one today — which is exactly what was said about the CSS colour before one turned
    up. Pattern is now `(?<!&)#(\d{1,4})(?![0-9a-fA-F])`, and both guards are pinned by assertions.
  - `pytest tests/test_no_dead_issue_refs.py` 3 passed; `ruff check` clean.
  - Set: **256 members, 151..908**, and `115 not in` it.

## What the boundary version got wrong, measured

`FIRST_DEAD = 115` shipped in `!171`. GitLab issued **#115** the same day. So:

| | boundary | closed set |
|---|---|---|
| live `#115` | **flagged as dead** | passes |
| needs re-tuning as GitLab grows | **yes, on every pass of the constant** | not periodically — one deliberate deletion when GitLab reaches #151 |
| silencing it | move one constant, invisible | delete a set member, RED |
| CSS colour `#475569` | **read as issue 475569** | ignored |

The CPO's standard for this cleanup was *"a better foundation now that does not require us to do
that same cleanup again in the future"*. A constant that must be re-tuned every time a counter
passes it fails that by construction, which is why this is a rewrite and not a bump to 116.

## How the false positive was found, since it matters more than the fix

`platform-reviewer` raised the hex-colour class on `!171` and called it hypothetical, having
grepped only the two guarded files: *"would false-positive on a pure-digit hex colour if one were
ever added"*. One already existed — `docs/roles/ui_expert.md`, `#475569` (slate-600).

It surfaced from REGENERATING the set rather than from review: the derived range ran to 475569,
which is not a plausible issue id, and the number was the tell. A review that reads only the files
in scope cannot see a class that lives outside them.

## What is NOT demonstrated, and one thing that cannot be

- **The set is NARROWER than the boundary in one real dimension.** It covers only GitHub numbers
  this repo already references, so a dead number never cited before — pasted in later from an old
  branch or the dead GitHub remote — is not caught, and the failure is SILENT. The boundary version
  did cover that. What decides the trade is which failure has actually happened: the boundary
  flagged a live issue within hours (#115), while the dead references that got in did so by being
  copied from elsewhere in the repo, which the set covers. Stated as a trade, not a win.
- The collision case cannot be demonstrated until GitLab reaches #151. What IS demonstrated is that
  it fails loudly and the fix is a deliberate, digest-breaking edit.
- **Two regex limitations are ACCEPTED and pinned, not fixed** — the same ambiguity from both
  sides, because `#217` is textually a dead issue AND a valid 3-digit CSS colour, and `#217e` is
  textually a dead issue AND a valid 4-digit `#RGBA` colour:
  · `_dead_refs("accent colour #217 was chosen")` → `[217]` — a **false positive**, loud.
  · `_dead_refs("see #217e for details")` → `[]` — a **false negative**, silent.
  Every context rule that fixes one worsens the other. Both are asserted as current behaviour by
  `test_a_short_all_digit_hex_colour_is_a_KNOWN_false_positive` and
  `test_a_reference_abutting_a_hex_letter_is_a_KNOWN_false_negative`, so a later "fix" has to
  break a named test and decide deliberately. `grep -P "#\d{1,4}[a-fA-F]"` over both guarded files
  matches nothing today.
  ⚠ These were in the tests and the contract but NOT here until round 7 — the third time on this
  branch a limitation was disclosed in some artifacts and not others.
- ⛔ **THE CPO QUOTE IN THE CONTRACT CANNOT BE CORROBORATED, AND THAT IS STRUCTURAL.**
  `scope-auditor` FAILed it twice: first as unlogged, then — after I logged it — on the deeper
  ground that an entry I wrote, in the branch under review, after being caught, proves only that I
  assert it. That objection is unanswerable and applies to EVERY entry in `escalations.log`: the
  file the working agreement calls the durable record of the CPO's rulings is authored by the party
  it constrains. This branch responds by not leaning on the quote at all — the justification is the
  technical argument that no value of the constant is both correct and stable, which anyone can
  check. The self-attestation problem is recorded against step 4 on GitLab #115.
