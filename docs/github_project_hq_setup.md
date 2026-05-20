# GitHub Project HQ Setup (Single-URL Operating Mode)

## Goal

Operate the agent company from one primary URL: your GitHub Project board.

Use the board as the command center for:
- idea intake
- decision-needed queue
- delivery status
- roadmap visibility

---

## Primary URL to bookmark

Create one Project and bookmark its URL as your daily home.

- User projects list: `https://github.com/users/ramialfahham/projects`
- Repo: `https://github.com/ramialfahham/football-data-pipeline`

After creating your Project, that project URL is your one main UI.

---

## 10-minute setup checklist

1. Open `https://github.com/users/ramialfahham/projects`.
2. Create a new Project (Table layout).
3. Name it `Matchday IQ - HQ`.
4. Add description: `Single control plane for ideas, delivery, and founder decisions.`
5. Add the fields below.
6. Create the views below.
7. Enable built-in project workflows:
   - Auto-add to project (issues + PRs from this repository)
   - Item added to project -> set `Status=Todo`
8. Save views and pin `HQ Today` as the default view.

---

## Required fields

Create these custom fields in the Project:

Core only (lightweight):

- `Status` (single select): `Todo`, `In Progress`, `Review`, `Done`, `Blocked`
- `Type` (single select): `Idea`, `Decision`, `Task`, `Bug`, `PR`
- `Priority` (single select): `P0`, `P1`, `P2`, `P3`
- `Decision Needed` (single select): `No`, `Yes`
- `Target Date` (date)

Optional (add later only if needed):

- `Role Owner` (single select)
- `Track` (single select)
- `Cost Impact` (single select)
- `Iteration` (iteration field)

---

## Required views (interactive)

## 1) HQ Today (Board) - default view

Purpose: one-screen daily control.

- Layout: Board
- Group by: `Status`
- Filter:
  - `is:open`
  - `Status:Todo,In Progress,Review,Blocked`
- Sort: `Priority` ascending (`P0` first), then `Target Date`

## 2) Decision Queue (Table)

Purpose: only items requiring your direct call.

- Layout: Table
- Filter:
  - `label:decision-needed` OR `Decision Needed:Yes`
  - `is:open`
- Visible fields:
  - `Priority`, `Target Date`, `Status`

## 3) Idea Funnel (Table)

Purpose: intake, triage, scoring, selection.

- Layout: Table
- Filter:
  - `label:idea`
  - `is:open`
- Group by: `Priority`
- Sort: `Target Date`

## 4) Delivery (Board)

Purpose: implementation flow.

- Layout: Board
- Filter:
  - `-label:idea`
  - `is:open`
- Group by: `Status`

## 5) Roadmap (Roadmap)

Purpose: high-level sequencing and communication.

- Layout: Roadmap
- Date field: `Target Date`
- Group by: `Type`

---

## How conversations work (with "employees")

- Start from the Project item.
- For strategic direction: comment on the linked Issue.
- For implementation review: comment on the linked PR.
- For active execution sessions: use Cursor chat and link the issue/PR back into the Project item.

This keeps one source of truth while still allowing deep work threads.

---

## Operating policy

- All new ideas must be created through `Idea intake` issue form.
- All founder decisions must use `Decision needed` issue form.
- If `Decision Needed=No`, agents continue autonomously.
- Keep one active `Now` objective and enforce WIP limits from `docs/agent_company_roadmap.md`.
- Prioritize quality descriptions over metadata: every ticket must clearly state why it matters, exact scope, and done criteria.

---

## Notes

- GitHub Project setup itself is UI-configured (not fully stored in-repo), so do this once manually.
- Issue forms and PR gates in this repo are now configured to support this operating mode.
