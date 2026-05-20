# Cursor Dispatch Workflow (Low-Touch Mode)

## Goal

Reduce founder operator time to one short daily check while keeping strict decision control.

---

## What is automated now

The workflow `.github/workflows/cursor-dispatch.yml` runs hourly (and on manual trigger) and:

1. Ensures routing labels exist: `ready-for-agent`, `agent-running`, `dispatch-queue`, `decision-needed`, `blocked`.
2. Selects open issues that are:
   - labeled `ready-for-agent`
   - not labeled `decision-needed`
   - not labeled `agent-running`
   - not labeled `blocked`
3. Marks selected issues with `agent-running`.
4. Updates one open issue titled `[Dispatch Queue] Cursor batch kickoff` with the current batch.

---

## Who creates issues?

Not only you.

- `CPO (you)` creates strategic idea issues and decision calls.
- Agents can create execution follow-up issues (implementation slices, bugs, or technical subtasks) when needed.
- System workflows maintain the dispatch queue issue automatically.

Rule: keep strategic intent in parent issues, allow agents to create execution children when it improves delivery clarity.

---

## Minimal daily routine

1. Open the Project board (`HQ Today`) and `[Dispatch Queue] Cursor batch kickoff`.
2. Confirm `Decision Needed` items are handled first.
3. Launch one batch Cursor run against the queue issue.
4. Review PRs from that batch only.

This keeps execution continuous while your focus stays on roadmap and decisions.

---

## Label semantics

- `ready-for-agent`: ticket is clear and ready for implementation.
- `agent-running`: ticket already dispatched/active.
- `decision-needed`: founder decision required before implementation.
- `blocked`: cannot proceed due dependency or unresolved question.
- `dispatch-queue`: system-managed queue issue label.

---

## Important limitation

This setup automates issue routing and queue generation. Cursor coding sessions still need a kickoff action from a human operator today.

If you later want true zero-touch execution, add an executor integration that can start coding agents directly from GitHub workflow events.
