# Task contract — CLAUDE.md: what the mirror token needs when it is renewed

objective: >
  One sentence added to the GitHub-mirror bullet in `CLAUDE.md`: the token is a fine-grained
  personal access token, it expires, and its replacement needs Contents AND Workflows
  read/write on the one repository — without Workflows GitHub rejects the mirror push because
  `.github/workflows/README.md` counts as a workflow. Today that fact lives only in the
  handover, which is rewritten every session.

refs: >
  CPO in chat, 2026-09-18: "go ahead as recommended", to the recommendation "one sentence in
  the mirror bullet of `CLAUDE.md`". The rejection itself was observed on the first mirror
  sync, 2026-09-18 (`refusing to allow a Personal Access Token to create or update workflow
  .github/workflows/README.md without workflow scope`).

scope_paths:
  - CLAUDE.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The home is `CLAUDE.md`, not `.github/workflows/README.md`: the same bullet already says
  where the token lives and who handles it, and it is not a protected path. The expiry date is
  not written — a date in a durable file goes stale; the sentence says the token expires and
  where the date is read (GitLab's mirror row shows a red error when it lapses).

decisions_reserved:
  - none.

done_when:
  - `git diff --stat gitlab/main -- CLAUDE.md` shows one bullet changed; the added text names both permissions and the reason.
  - `python -m pytest tests/test_governance_doc_parity.py tests/test_no_dead_issue_refs.py -q` green.

amendments: (none)
