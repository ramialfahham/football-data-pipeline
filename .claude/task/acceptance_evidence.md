# Acceptance evidence — the design chain and the ruling log in CLAUDE.md

Measured with grep against the files as committed, not asserted.

criteria_demonstrated:
  - ⭐ THE DEFECT, MEASURED BEFORE THE FIX. `grep -c` over `CLAUDE.md` — the file every session is
    told to read first — returned **0** for all five of `wireframes`, `metrics_display`,
    `ui_design_brief`, `design-mocks` and `escalations.log`. The orientation file named the data
    contract, the layer rules, the metric layer, ops, dev workflow, guardrails, site IA and the
    dormant GitHub tree, and pointed at the design chain nowhere and at the CPO ruling record
    nowhere. After: all five return non-zero.
  - THE AUTHORITY TABLE NAMES THE DESIGN CHAIN AND POINTS AT ONE OWNER for its reading order —
    `docs/wireframes/00_overview.md` — rather than restating the order itself.
  - THE AUTHORITY TABLE NAMES `.claude/task/escalations.log` as the durable record, with the rule
    that "you ruled X" needs a quote from it and that a task contract is overwritten while this file
    is not.
  - THE PRECEDENCE IS STATED ONCE. `grep -ci 'which wins|beats every|on conflict'`:
    **`CLAUDE.md` = 0, `00_overview.md` = 2.** The rule lives in one file; the other points.
  - `00_overview.md`'S READING ORDER IS COMPLETE. It named three of the six documents that govern
    what a screen shows — brief, site architecture, wireframes — and omitted
    `content_architecture.md`, `metrics_display.md` and the mock/issue layer. Now a six-row table,
    one row per question, plus the conflict rule.
  - EVERY LINK RESOLVES. All eight paths referenced by the new table exist on disk, checked with
    `test -f`: `00_overview.md`, `escalations.log`, `ui_design_brief.md`, `site_architecture.md`,
    `content_architecture.md`, `metrics_display.md`, `design-mocks/README.md`,
    `99_gaps_register.md`.
  - THE OFFLINE GATES ARE GREEN. No code changed, so this is a formality — run and recorded rather
    than assumed.

## The defect this branch shipped and had caught

⛔ The replacement reading order quietly REWROTE the conflict rule. `00_overview.md` said
**"Conflicts escalate to the CPO."** — absolute — and my version said a logged ruling wins, "below
that, the more specific and more recent wins", and only leftovers escalate. That is a §10 rule
extension: it invents an auto-resolution and narrows when the CPO is consulted. The contract
simultaneously claimed "nothing is deleted". `scope-auditor` FAILed both.

Reverted. The rule is absolute again, in force and in wording, with no tie-breaker. The only thing
added beside it is that a ruling already in `escalations.log` is not a conflict but the answer —
which changes nothing about escalation. Verified: `grep -c "more specific and more recent"` = **0**.

⚠ Worth naming the shape, because it is not carelessness: that sentence reads like tidying. "More
specific and more recent wins" is a sensible-sounding default in the abstract, which is exactly why
it slipped past me — it is a decision about who decides, dressed as a formatting improvement.

## The trade I made, stated so a reviewer can push on it

The chain's MEMBER LIST is now in both files. A document joining the chain needs both updated.

I wrote the non-duplicating version first — `CLAUDE.md` naming only `00_overview.md` — and reverted
it, because it dropped three of the five terms back to a grep count of **0** in the always-loaded
file. A pointer only helps a reader who follows it, and #41 is the proof: the wireframes were
reachable the whole time and I did not reach them.

What is NOT duplicated is the RULE. "Which document wins" appears zero times in `CLAUDE.md`. A stale
filename list is visible on the next read; a precedence rule stale in two places is the failure that
cost the last two MRs their review rounds.

## What is NOT demonstrated

- **That this works.** The defect it addresses — a page rebuilt without reading its design — is not
  machine-detectable, and nothing here is enforced by a gate. The only evidence that would count is
  the NEXT page being built from its issue and wireframe without being told to. That is the player
  page, and it is the test.
- Nothing is deleted or reworded in either file beyond the additions, so no existing claim needed
  re-verifying.
