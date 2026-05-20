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
5. Updates one open issue titled `[Dispatch Status] Cursor automation heartbeat` with live counts.

---

## Who creates issues?

Not only you.

- `CPO (you)` creates strategic idea issues and decision calls.
- Agents can create execution follow-up issues (implementation slices, bugs, or technical subtasks) when needed.
- System workflows maintain the dispatch queue issue automatically.

Rule: keep strategic intent in parent issues, allow agents to create execution children when it improves delivery clarity.

---

## Minimal daily routine

1. Open the Project board (`HQ Today`) and `[Dispatch Status] Cursor automation heartbeat`.
2. Confirm `Decision Needed` items are handled first.
3. Check `[Dispatch Queue] Cursor batch kickoff` for the exact active batch list.
4. Launch one batch Cursor run against the queue issue.
5. Review PRs from that batch only.

This keeps execution continuous while your focus stays on roadmap and decisions.

---

## Label semantics

- `ready-for-agent`: ticket is clear and ready for implementation.
- `agent-running`: ticket already dispatched/active.
- `decision-needed`: founder decision required before implementation.
- `blocked`: cannot proceed due dependency or unresolved question.
- `dispatch-queue`: system-managed queue issue label.
- `dispatch-status`: system-managed progress heartbeat issue label.

---

## How to know if progress is happening

Use `[Dispatch Status] Cursor automation heartbeat`:

- `Running now` > 0 means issues are actively in queue (`agent-running`).
- `Picked this run` > 0 means the latest dispatch moved new tickets forward.
- `Ready backlog` shows how many ready tickets are still waiting.
- `Decision-needed` and `Blocked` show why some tickets are not moving.

Board columns are synchronized by `project-status-sync` (see `docs/project_status_sync.md`).

---

## Important limitation

This setup automates issue routing and queue generation. Cursor coding sessions still need a kickoff action from a human operator today.

If you later want true zero-touch execution, add an executor integration that can start coding agents directly from GitHub workflow events.
