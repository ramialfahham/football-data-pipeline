# Review — fix/build-memory-one-payload

diff_sha256: 446c69b45298de01ad697daf5c5b647e46c5b15c2938911173068b76e12bd74f

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; format.ts joined by an amendment that names its approval and its measured basis; nothing reserved (the incremental build, the runner size, #175/#176, the competition payloads) is touched.
- Route params and slugs, metric formats and labels are unchanged; the declaration of no new mechanism and no recurring cost matches the diff.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed on evidence files left from the previous task; round 2 read this branch's evidence: a byte compare with main's build, 0 files differ on the committed sample (2,543 files) and at full scale (198,999 files), and the design check at 375, 700 and 1010px with 0 failures and main's 27 warnings.
- Both pages read their own file at render and carry only file name, slug, league code and locale as route data; format.ts builds every Intl formatter in two cached helpers keyed by locale and options; no field, label, metric or order changes.

## platform-reviewer
VERDICT: PASS
risks_checked:
- readDist keeps its default, so check-built-pages still gets the HTML; pass 1 yields the same path set; structuredClone exists on the pinned Node 24 and copies only plain data; the SEO check still fails the build closed.
- The page reads use the same process.cwd() and node:fs pattern as before; the formatter caches are bounded by the literal option sets in format.ts and formatters hold no state.

## escalations
- question: A memory peak outside the two planned fixes (about 7.8 GB outside the heap during page writing, traced to a new Intl formatter per call in src/lib/format.ts) — fix it in this MR or in a separate issue?
  CPO ANSWER: in this MR; approved in chat, 2026-10-10.
