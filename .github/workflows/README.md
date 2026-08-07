# These workflows are DORMANT. Nothing here runs.

**Status as of 2026-08-06.** CI for this repository is `.gitlab-ci.yml` at the repo root.
Every workflow in this directory is inert: GitHub Actions execute none of them.

This file exists because a dormant workflow and a live one look identical, and the eleven `.yml`
files here were last edited 2026-07-28, while they were still running. Nothing in the tree said
they had stopped.

## Why

The project migrated from GitHub to GitLab in 2026-08, after the GitHub account was suspended.
The six quality gates, the nightly production build and the v2 site deploy were translated into
`.gitlab-ci.yml` and run there.

**The GitHub repository is deliberately KEPT.** CPO ruling, 2026-08-06: the repo stays, and how it
gets used is decided once account access returns. So these files are **not deleted, not moved and
not edited** — re-activating any of them should be a decision, not a reconstruction.

## What is here

**Dormant because the platform is dormant** — these ran until the migration:

| Workflow | GitLab equivalent |
|---|---|
| `ci-validate.yml` | `validate:governance` |
| `python-ci.yml` | `test:python` |
| `security-secrets.yml` | `validate:secrets` |
| `ci-ui.yml` | `validate:ui` |
| `ci-site-v2.yml` | `build:site-v2` |
| `ci-data-build.yml` | `data:build:mr` / `data:build:main` |
| `dbt-scheduled.yml` | `data:nightly` |
| `deploy-site-v2.yml` | `deploy:export` + `deploy:site-v2` |
| `board-request-sync.yml` | **none** — drove a GitHub Projects board that did not migrate |
| `ci-failure-watchdog.yml` | **none** — GitLab notifies on pipeline failure natively |
| `pages-match-preview.yml` | **none, deliberately** — see below |

`pages-match-preview.yml` is the one worth knowing about. It carried a daily `cron` that ran a
**production BigQuery build** and deployed the legacy card MVP. That product was **retired on
2026-07-21** — taken offline, its Pages deployment deleted, `site/` frozen — and this workflow was
never touched at retirement. It was dormant-by-decision before it was dormant-by-platform, and it
was deliberately not translated: porting it would have resurrected a retired product and
reinstated a recurring cost.

**Dormant by decision, before the migration** — `_paused/`:

- `cursor-dispatch.yml`
- `pr-autopilot.yml`
- `project-status-sync.yml`

Those two categories are not the same thing and are not merged here. One stopped because someone
decided it should; the other stopped because the platform did.

## ⚠ If GitHub comes back — READ THIS BEFORE PUSHING ANYTHING

**These workflows are dormant, not disabled.** Nothing was turned off; the platform stopped
running. So re-activation is NOT an act of enabling — **the first ordinary push to the GitHub
`main` re-arms it.** Seven of the eleven trigger on `push: branches: [main]`:

`ci-data-build.yml` · `ci-site-v2.yml` · `ci-ui.yml` · `ci-validate.yml` ·
`pages-match-preview.yml` · `python-ci.yml` · `security-secrets.yml`

And two crons are still in the files, untouched: `dbt-scheduled.yml` (04:00 UTC) and
`pages-match-preview.yml` (07:30 UTC).

**THREE of these write PRODUCTION BigQuery** — `dbt-scheduled` and `pages-match-preview` via
`target: prod` in the profile, `ci-data-build` via `--target prod` on the CLI (its profile default
is `ci`):

| Workflow | What it does to prod |
|---|---|
| `ci-data-build.yml` | `dbt seed` + `dbt build --selector staging` + `--selector downstream` + `dbt test`, on any non-`pull_request` event — **so a push to `main` runs it**, plus a bootstrap ingest that spends API-Football calls. Additionally gated on `needs.changes.outputs.data`, so a docs-only push does not fire it — do not rely on that, since the path set includes `ingestion/**`, `scripts/check_*.py` and `dbt_project/*.yml` |
| `dbt-scheduled.yml` | the full nightly: ingest, seed, `dbt build` |
| `pages-match-preview.yml` | a prod dbt build **with no `new_data` gate**, so it rebuilds unconditionally — then deploys the MVP **retired 2026-07-21** back to Pages |

`ci-data-build.yml`'s own comment names the count: the prod arm joins `prod-warehouse-write`,
*"shared with dbt-scheduled + pages, so the three prod-writers never MERGE the bare prod tables
concurrently (#667)"*.

**The concurrency group does not protect you across platforms.** `.gitlab-ci.yml` serialises its
prod writers through `resource_group: prod-warehouse-write`; a GitHub job writing prod is outside
that group entirely, so it can merge the bare prod tables while GitLab is mid-build.

So a single catch-up push to a reactivated GitHub remote can, with nothing else done: run a full
prod warehouse build concurrently with GitLab's, spend API quota, and republish a retired product.

**Before any push to a reactivated GitHub remote**, disable the workflows in the repository
settings or move them into `_paused/` FIRST. Cost is a CPO decision (`CLAUDE.md`, "Cost is
non-negotiable"), and two schedulers writing one warehouse is a cost change and a correctness
hazard, not just a duplicate bill.

## Do not

- **Do not treat this directory as the CI reference.** Read `.gitlab-ci.yml`.
- **Do not "tidy" it** by deleting workflows or merging `_paused/` into the top level. The tree is
  kept in the state it stopped in, on purpose.
- **Do not edit a workflow to "keep it in sync"** with a GitLab change. They are a snapshot of what
  ran on GitHub, not a second copy to maintain. Divergence is expected.
