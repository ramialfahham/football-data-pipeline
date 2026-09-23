# Review — docs/address-words — 2026-09-23

diff_sha256: 46e201c33b1ceec703eb5fe55d89501d3a4f2dbb680336878a39154e89a1ba89

rounds: 2

Round 1 passed the first word list, which turned out to be unresearched. The CPO asked; research and
an independent search assessment followed; he accepted its list and asked how it holds for pages
not designed yet. Round 2 rewrote the list, marked planned pages provisional and removed a reason
the document had attributed to him. Delta review, PASS.

Rebound after the rebase onto main (the cleanup, !223, merged first). The three task artifacts were
the only conflicts and were resolved to this task's side; `docs/site_architecture.md` and
`.claude/task/contract.md` are byte-identical to the reviewed commit (`git diff f8be58ec HEAD`
empty), so the verdict stands and only the binding moves with the new base.

## scope-auditor
VERDICT: PASS
risks_checked:
- The reason "collided with the metric glossary's word", which the CPO said was never his, is gone from both files, not reworded.
- No line presents two words for one page as current: the remaining `fixtures`/`rankings` mentions are marked as the built site's old addresses, not yet switched.
- Naming and URL decision rights: the settled words carry his dated acceptance in the contract's refs; the provisional words, the glossary question and the match-date question stay in `decisions_reserved` and are marked provisional or open in the document itself.
- The settled/provisional split in the word table matches the pages built today; `standings` and `h2h` are provisional only.
- Scope: the same two files as round 1, both in `scope_paths`; prose only, no mechanism, no cost, no credential.
- Round 1, unchanged since: the direction carries his dated answer; the prior tab rulings' "every locale" half is disclosed as replaced; no impact map needed for a document.

## escalations
(none)
