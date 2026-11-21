# Review — claude/36-img-origin-pin — 2026-11-21

diff_sha256: e8d9e49f8fa706063e6e5f98735f86e60786d348e03491356a23a7b62d3a63d1

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3 delta: the three strip-only core-document lines in docs/site_architecture.md and docs/ui_design_brief.md fix the round-2 doc-sync FAIL; each edit is a pure deletion, and a grep finds no other stale photo claim in the three architecture and brief documents.
- Core text routes through the MR head and the CPO's merge (working_agreement §10); the contract names the lines in decisions_taken and the two documents are in scope_paths.
- No new mechanism, dependency or recurring cost: the change extends the existing built-pages check.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Pin semantics: a pin at 0 fails on every build; a pin above 0 fails a sample build in both directions and is only reported on a full export; the manifest branch of main is covered by a test.
- Image extraction covers img, source, srcset, og:image, twitter:image and JSON-LD image and logo; host classification rejects lookalike hosts; an unparseable address fails closed.
- Round 3 delta: three comment edits, three doc deletions and one test on the default pins; no build, hook, workflow or dependency change.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Built output of the committed sample: player rows and the player header show initials with no image; the player page has no og:image, twitter:image or JSON-LD image; no built page names a provider player or coach photo.
- No metric, label, string or field is added; PlayerRow no longer accepts a photo prop and no caller passes one.
- Round 3 delta: the stale comments say initials; the doc lines only drop the word photo.

## escalations
(none)
