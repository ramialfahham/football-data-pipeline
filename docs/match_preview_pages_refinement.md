# Match Preview (GitHub Pages) — refinement guide

This doc explains each decision, the options, and a **recommended default** (trust-first, low noise, good for sharing).  
**Clickable choices:** use the **Refinement** form the assistant sends in chat (Cursor AskQuestion). Your selections can then be copied into the implementation plan.

---

## A. Hosting and URL

### A1. How is the site published?

| Option | What it means |
|--------|----------------|
| **GitHub Actions → Pages artifact** | Workflow builds a small folder (`index.html` + JSON), uploads it as a Pages deployment. **No** need to commit `matchday_insights.json` on every refresh. |
| **Files under `docs/` on `main`** | You commit HTML + JSON each update. Pages serves from `/docs`. Simpler mentally, but **noisy git history** and mixes with your existing Markdown in `docs/`. |

**Recommendation:** **Actions artifact** — cleaner repo, same public URL.

### A2. URL path

| Option | What it means |
|--------|----------------|
| **Site root (`/`)** | `https://<user>.github.io/<repo>/` is only this app. |
| **Subpath (`/match-preview/`)** | App at `.../repo/match-preview/`. Leaves room for a future homepage at `/`. |

**Recommendation:** **`/match-preview/`** — fewer future migrations.

### A3. Repo / Pages visibility

| Option | What it means |
|--------|----------------|
| **Public repo + public Pages** | Anyone with the link can see data (expected for this prototype). |
| **Private / access-controlled** | Needs different hosting or GitHub plan features. |

**Recommendation:** **Public** for v1 unless you have a compliance constraint.

### A4. Custom domain

| Option | What it means |
|--------|----------------|
| **Later** | Use `*.github.io` first. |
| **Now** | DNS CNAME to GitHub Pages; extra setup step. |

**Recommendation:** **Later** until the app is stable.

---

## B. Automation and data

### B1. How often should the public site refresh?

| Option | What it means |
|--------|----------------|
| **Twice daily** | Closer to your `dbt-scheduled` idea; more BQ + Actions minutes. |
| **Once daily** | Usually enough for pre-match cards. |
| **Manual only** | `workflow_dispatch` until you trust the pipeline. |

**Recommendation:** **Once daily** + **manual** trigger — good balance of freshness vs. cost.

### B2. What does the Pages workflow build in BigQuery?

| Option | What it means |
|--------|----------------|
| **Mart only** | `dbt build --select mart_matchday_insights` — fast, assumes upstream tables are already fresh from your main scheduled job. |
| **Broader build** | Refreshes more of the DAG before export — slower, costlier, fewer “stale upstream” surprises. |

**Recommendation:** **Mart only**, with a **comment in the workflow** that the main schedule keeps facts/marts fresh.

### B3. If the workflow fails (dbt or JSON extract)

| Option | What it means |
|--------|----------------|
| **Keep last successful deploy** | Visitors still see yesterday’s data instead of a broken site. |
| **Deploy “unavailable” page** | Clear signal of failure; wipes good data from view. |

**Recommendation:** **Keep last successful deploy**.

### B4. `dbt show` row limit (CLI cap)

`dbt show` only previews a capped number of rows; it is **not** a business “window” (that lives in the mart SQL). The cap should match **how many rows this mart can return for one export**: `mart_matchday_insights` is one row per upcoming fixture on the selected matchday, so for **Bundesliga** (internal `league_code` **D1**) that is **at most nine**.

**Recommendation:** **`--limit 9`** for Bundesliga-only exports. If you later export a league with more fixtures per round, raise the cap to match that round’s maximum (or switch to a warehouse query without a CLI row cap).

---

## C. Visual design (mock)

### C1. Background / atmosphere

| Option | What it means |
|--------|----------------|
| **Full mock** | Green→black gradient, subtle texture/noise, corner “spotlights” (CSS). |
| **Simplified** | Dark green / near-black, minimal effects — faster build, easier contrast tuning. |

**Recommendation:** **Full mock** for share impact; simplify if QA finds contrast issues.

### C2. “VS” styling

| Option | What it means |
|--------|----------------|
| **Metallic look (CSS)** | Gradient text / highlights to echo the draft. |
| **Flat bold white** | Easier, still strong. |

**Recommendation:** **Flat bold first**; upgrade to metallic if time allows.

### C3. Chevrons and pagination dots

| Option | What it means |
|--------|----------------|
| **Always visible** | Obvious navigation for casual viewers. |
| **Chevrons subtle until hover/tap** | Cleaner look; slightly less discoverable. |

**Recommendation:** **Always visible** on mobile.

### C4. Sparkle / info control (bottom-right in mock)

| Option | What it means |
|--------|----------------|
| **Info icon → modal** | Short read-only text: what the 5-Spieltage window is, data source, no “AI”. |
| **Omit v1** | Ship faster. |

**Recommendation:** **Info modal** — builds trust without inventing metrics.

### C5. Number font

| Option | What it means |
|--------|----------------|
| **Tabular monospace** | Aligned columns, “data” feel. |
| **Proportional bold (mock-like)** | Softer, more “poster”. |

**Recommendation:** **Tabular monospace** for alignment.

---

## D. Hero row (draft had “win probability”)

We **do not** ship fabricated win probability.

| Option | What it means |
|--------|----------------|
| **No extra row** | Only the **10** backed metric rows. Clearest story. |
| **Schussanteil bar** | One horizontal split bar built only from `home_shot_share_recent` / away share. |
| **Punkte bar** | Only if we define an honest split from **existing** fields (more design work). |

**Recommendation:** **No extra row** for v1; add Schussanteil bar in v2 if you want the mock punch.

---

## E. Copy and numbers (DE)

| Topic | Options | Recommendation |
|--------|---------|----------------|
| Language | DE only vs DE+EN later | **DE only** v1 |
| Decimals | Comma vs dot | **Comma** (DE) |
| Percents | 1 decimal vs integer | **One decimal** |
| Formula lines | 2-line clamp vs free wrap | **`line-clamp: 2`** |
| Global footnote | Yes vs no (“Fenster = …”) | **Yes** under metric block |
| Bar labels (if bar later) | DE only vs DE+small EN | **DE only** |

---

## F. League rank on the card

| Option | What it means |
|--------|----------------|
| **Under each team name** | “Platz 3” style under home / away. |
| **One combined line** | “Platz 3 vs Platz 7” in one line. |
| **Hide when both null** | No empty chrome if standings missing. |

**Recommendation:** **Under each name**, **hide the line when that side’s rank is null**.

### Rank data source

Use **`mart_team_season.latest_rank`** (from standings snapshot join; can be null if snapshot missing).
Derived calculated rank (points/goal diff) will be part of the domestic_league standings mart when built.

---

## G. Winner coloring (green / slate)

| Topic | Options | Recommendation |
|--------|---------|----------------|
| Tie | Exact only vs epsilon band | **Exact tie** = neutral both sides |
| No games in window | Grey both vs dashes | **`—`** values, **neutral** colors |
| Points row (which number to compare) | Raw sums vs `points_capture_recent` vs no color | **`points_capture_recent`** for fair comparison |
| WCAG on green | Strict AA vs best effort | **Best effort** v1, fix obvious fails in QA |

---

## H. Privacy and extras

| Topic | Recommendation |
|--------|----------------|
| Analytics on public site | **None** v1 |
| Feedback (Apps Script) on public site | **None** v1 (secrets + scope) |
| JSON shape | **Flat `show[]`** — matches current export script |
| Logos | **Add URLs to mart** — single source of truth |
| HTML in repo | **`site/match-preview/`** |
| Mock PNG in repo | **Commit** to `docs/design/` when available |

---

## Where the full technical plan lives

Cursor plan file (implementation outline, DAG, file paths):

`c:\Users\Rami\.cursor\plans\gh_pages_match_preview_bce3ad94.plan.md`

This Markdown file is the **human-readable refinement + recommendations** companion; use the **in-chat AskQuestion** block for **clickable** answers.
