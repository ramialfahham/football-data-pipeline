# These workflows are DISABLED. Nothing here runs.

**Status as of 2026-09-18.** CI for this repository is `.gitlab-ci.yml` at the repo root.
GitHub Actions are **disabled at the repository level** (Settings → Actions → General → *Disable
actions*), so every workflow in this directory is inert whatever its triggers say.

This file exists because a disabled workflow and a live one look identical, and the eleven `.yml`
files here were last edited 2026-07-28, while they were still running. Nothing in the tree said
they had stopped.

## Why

The project migrated from GitHub to GitLab in 2026-08, after the GitHub account was suspended.
The six quality gates, the nightly production build and the v2 site deploy were translated into
`.gitlab-ci.yml` and run there.

**The GitHub repository is a read-only mirror of `main`.** CPO ruling, 2026-09-18, once the account
was back: GitLab stays the system of record (CI, MRs, issues, the WIF binding); GitLab pushes
`main` — and only `main` — to GitHub after every merge (a push mirror, *Mirror only protected
branches*); nothing is pushed there by hand, nothing is opened or merged there, and Actions stay
off. These files are **not deleted, not moved and not edited** — they are the record of what ran
before the migration, and re-activating any of them would be a decision, not a reconstruction.

## What is here

**Stopped by the migration** — these ran until it:

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

**Paused by decision, before the migration** — `_paused/`:

- `cursor-dispatch.yml`
- `pr-autopilot.yml`
- `project-status-sync.yml`

Those two categories are not the same thing and are not merged here. One stopped because someone
decided it should; the other stopped because the platform did.

## ⚠ Why Actions must STAY disabled — read this before touching the setting

**The mirror pushes to GitHub `main` after every merge, and seven of the eleven workflows trigger
on `push: branches: [main]`.** With Actions enabled, the mirror sync itself would run them; the
repository-level *Disable actions* setting is the only thing standing between a routine merge on
GitLab and the runs below. It was checked before the first sync on 2026-09-18. The seven:

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

So one mirror sync with Actions enabled can, with nothing else done: run a full prod warehouse
build concurrently with GitLab's, spend API quota, and republish a retired product.

**Re-enabling Actions is therefore a CPO decision, never a click.** Cost is his (`CLAUDE.md`,
"Cost is non-negotiable"), and two schedulers writing one warehouse is a cost change and a
correctness hazard, not just a duplicate bill. If GitHub is ever to run anything again, the
workflows are moved into `_paused/` or rewritten FIRST, and the setting is flipped last.

## Do not

- **Do not treat this directory as the CI reference.** Read `.gitlab-ci.yml`.
- **Do not "tidy" it** by deleting workflows or merging `_paused/` into the top level. The tree is
  kept in the state it stopped in, on purpose.
- **Do not edit a workflow to "keep it in sync"** with a GitLab change. They are a snapshot of what
  ran on GitHub, not a second copy to maintain. Divergence is expected.
