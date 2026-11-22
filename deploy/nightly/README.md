# The nightly on Cloud Run — deploy and operate

GitLab **#39 Stage 1**. Moves the nightly pipeline out of GitLab CI onto
`Cloud Scheduler → Cloud Run Job → BigQuery`.

**Why:** the nightly is a *production* job — it keeps the product's data fresh. Running it in
CI meant a CI-side event took the product offline, twice in four days: the GitHub→GitLab
migration silently dropped the cron (six days stale, unnoticed), then the namespace hit
`ci_quota_exceeded`. At ~111 minutes per run against a 400 min/month allowance shared across
three projects, it never fit. Daily refresh is the product's minimum, so cadence was not
available as a lever — the hosting had to change.

| | |
|---|---|
| GCP project | `football-data-pipeline-gcp` |
| Region | `europe-west1` (BigQuery data is EU multi-region) |
| Job name | `fdp-nightly` |
| Service account | `github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com` |
| Schedule | `0 4 * * *` UTC |
| Cost | ~$1.70/month; ~$0.35 after #33 item 14 |

The service account is the one CI already impersonates, so it **already holds the BigQuery
roles**. Inside Cloud Run the job runs *as* it, so `method: oauth` + `google.auth.default()`
resolves credentials natively — no Workload Identity Federation exchange, no key file.

---

## One-time setup

### 1. The API key (do this first — the deploy references it)

`API_FOOTBALL_API_KEY` is a credential and must not be an env var in the job config, where it
is readable in plain text by anyone with `run.jobs.get` and survives rotation.

```bash
gcloud services enable secretmanager.googleapis.com
```

Create the secret and paste the value when prompted. Take it from the repo-root `.env`:

```bash
gcloud secrets create api-football-key --replication-policy=automatic --data-file=-
```

Then let the job read it:

```bash
gcloud secrets add-iam-policy-binding api-football-key \
  --member="serviceAccount:github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 2. Deploy the job

**As of GitLab #74, `build:nightly-image` + `deploy:nightly-image` in `.gitlab-ci.yml` do this
automatically** on every push to `main` that touches a path the image actually contains
(`*data_paths_image`) — the "the image never tracked `main`" defect this fixed. CI builds the
image with kaniko (no Cloud Build — see the job's own comment for why) and pushes it to
Artifact Registry, then repoints `fdp-nightly` at the new image with `gcloud run jobs update
--image=...`. The command below is now the manual fallback (initial setup, or a rebuild the
path filter did not catch), not the normal path to prod — it still works unmodified, since it
uses your own `gcloud` session's permissions, not CI's scoped-down service account.

Built remotely by Cloud Build from the `Dockerfile` at the repo root — **no local Docker
needed**. Run from the repo root:

```bash
gcloud run jobs deploy fdp-nightly \
  --source . \
  --region europe-west1 \
  --service-account github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com \
  --set-secrets API_FOOTBALL_API_KEY=api-football-key:latest \
  --cpu 1 --memory 2Gi \
  --task-timeout 3h \
  --max-retries 0
```

`--max-retries 0` is deliberate. The ingest lock (`ingestion/api_football/ingestion_lock.py`)
holds a lease on `RAW_APIF_INGEST_LOCK`, so an immediate retry would be refused and would only
add noise. Recovery is the next night — which is exactly why Stage 2 (freshness alerting,
#33 item 16) matters and why Stage 1 does not claim to close that gap.

`--task-timeout 3h` matches the CI job's timeout.

### 3. Schedule it

Scheduler needs permission to invoke the job. Bind it **on the job**, not on the project:

```bash
gcloud run jobs add-iam-policy-binding fdp-nightly \
  --region europe-west1 \
  --member="serviceAccount:github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

The project-scoped form (`gcloud projects add-iam-policy-binding … roles/run.invoker`) would let
this identity invoke **every** Cloud Run service and job in the project, present and future.
That matters more than usual here: `github-actions-dbt` is not a single-purpose identity — it is
the same account CI impersonates to write the prod warehouse. The resource-scoped binding above
grants exactly one capability: invoke `fdp-nightly`.

```bash
gcloud scheduler jobs create http fdp-nightly \
  --location europe-west1 \
  --schedule "0 4 * * *" \
  --time-zone UTC \
  --uri "https://run.googleapis.com/v2/projects/football-data-pipeline-gcp/locations/europe-west1/jobs/fdp-nightly:run" \
  --http-method POST \
  --oauth-service-account-email github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com
```

### 4. Pause the GitLab schedule

**Required, and easy to forget.** Otherwise both fire at 04:00 once GitLab's quota resets on
the 1st. The BigQuery ingest lock would stop them corrupting each other — it is dataset-level,
not CI-level, so it already spans both platforms — but one of the two would fail every night
for no reason.

GitLab → **Build → Pipeline schedules** → pause the 04:00 schedule (id `4379625`).

`data:nightly` stays in `.gitlab-ci.yml` on purpose, reachable by manual web dispatch, as a
fallback until Cloud Run has proven itself. Removing it edits `.gitlab-ci.yml`, which the repo
guards, so it needs its own governance task — see `docs/working_agreement.md` §2.

---

## Monitoring — #39 Stage 2

**Why this is out-of-band.** Every check inside the nightly only runs when the nightly runs.
The failure that cost six days of stale data was the nightly **not running at all**, and no
in-pipeline test can ever see that.

**What is monitored is DATA AGE, not job success.** `scripts/check_raw_freshness.py` runs
hourly as its own Cloud Run Job, reads each raw table's last-modified time, and exits non-zero
when it is past the `error_after` already declared in `sources.yml`. Job success is only a
proxy — a pipeline that "succeeds" nightly while writing nothing is stale and would pass a
job-success check. Table age is the real signal.

Four policies, all wired to the same email:

| Policy | Fires when | Means |
|---|---|---|
| `fdp raw data is STALE or uncheckable` | the sentinel exits non-zero | **stale data (exit 1) OR we cannot tell (exit 2)** — read the log |
| `fdp freshness sentinel itself stopped` | no successful sentinel run in 3h | we can no longer *tell* |
| `fdp-nightly execution failed` | a nightly run dies | early warning, before staleness |
| `fdp-site execution failed` | a site deploy run fails | nothing was deployed, the live site shows the previous build |

**Cost: zero.** `client.get_table()` is a metadata call, not a query — no bytes scanned, no
query job. That is what makes hourly affordable without thinking about it.

### Why not simply alert on the nightly not running

That was the first design, and it hit a wall worth recording so nobody reaches for it again:

- `conditionAbsent` rejects any duration over **23h30m**; MQL `absent_for` rejects anything
  over **1d1h**. Both tried against the real API, both HTTP 400.
- For a **daily** job every value at or below 24h fires shortly before *every* run. So 25h was
  the only usable number — a ceiling, not a choice.
- An MQL condition also cannot share a policy with any other condition: *"Alert policies with
  monitoring_query_language condition type can only have a single condition."*

Running the **sentinel hourly** dissolves all of it: absence detection on an hourly job needs
only a 3h window, far inside the cap, and the staleness threshold itself is ours to set from
`sources.yml`.

`gcloud alpha monitoring` is not installed and does not need to be — the REST API is enough.

### Deploy the sentinel job

⚠ **ORDER MATTERS, and getting it wrong produces an alert storm.** The sentinel runs from the
nightly's image, so that image must already contain `scripts/check_raw_freshness.py`. As of
GitLab #74, step 2 below happens automatically (`build:nightly-image` +
`deploy:nightly-image` in `.gitlab-ci.yml`) —
the sentinel itself still does NOT follow it; it stays pinned to a fixed digest until it is
repointed by hand (step 3), a deliberate separate decision (see `.claude/task/contract.md` on
that branch). The sequence:

1. merge the branch that adds the script
2. the image rebuilds automatically on merge (or by hand:
   `gcloud run jobs deploy fdp-nightly --source . --region europe-west1`, from `main`)
3. point the sentinel at the new image (below)
4. **only then** create the schedule and the two sentinel alert policies

Doing 4 before 2 means the sentinel fails every hour on
`can't open file '/app/scripts/check_raw_freshness.py'`, and the "sentinel itself stopped"
policy pages every 3h. Verified the hard way: deploying against the pre-script image and
executing it produced exactly that error, with `exit(2)`.

One policy is deployed but deliberately **not** in `alert-policy.json`:
`fdp-nightly stale (no success in 25h)`, from the superseded job-success design. Keep it alive
as a bridge until the sentinel is running, then delete it — otherwise there is an unmonitored
window between the two designs. It is absent from the JSON because the JSON is the target
state, and re-applying the file must not recreate it.

Same image as the nightly — Cloud Run overrides the entrypoint, so there is no second build and
no second thing to keep in sync:

```bash
gcloud run jobs deploy fdp-freshness \
  --image "$(gcloud run jobs describe fdp-nightly --region europe-west1 --format='value(spec.template.template.containers[0].image)')" \
  --region europe-west1 \
  --service-account github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com \
  --command python --args scripts/check_raw_freshness.py \
  --cpu 1 --memory 512Mi \
  --task-timeout 5m \
  --max-retries 0

gcloud run jobs add-iam-policy-binding fdp-freshness \
  --region europe-west1 \
  --member="serviceAccount:github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud scheduler jobs create http fdp-freshness \
  --location europe-west1 \
  --schedule "7 * * * *" \
  --time-zone UTC \
  --uri "https://run.googleapis.com/v2/projects/football-data-pipeline-gcp/locations/europe-west1/jobs/fdp-freshness:run" \
  --http-method POST \
  --oauth-service-account-email github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com
```

`--max-retries 0`: a retry would re-check the same tables and reach the same answer. Staleness
is a state, not a transient error.

Minute `7` rather than `0` keeps it off the hour, where scheduler load and the nightly's own
04:00 start cluster.

**Exit codes are the alerting mechanism.** `0` fresh · `1` stale (past `error_after`) · `2`
could not check. `2` is deliberately not `0` — a sentinel that cannot check must never look
healthy, because that is indistinguishable from a working pipeline.

### Create the notification channel (once)

```bash
curl -s -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://monitoring.googleapis.com/v3/projects/football-data-pipeline-gcp/notificationChannels" \
  -d '{"type":"email","displayName":"fdp alerts","labels":{"email_address":"rami.fahham@gmail.com"}}'
```

**Google sends a verification email. Until it is clicked the channel exists but delivers
nothing** — so an unverified channel is a policy that looks armed and is not.

### Create the alert policies

`alert-policy.json` holds EVERY policy under `policies`, plus `_comment` keys for the reader.
The API rejects unknown fields, so strip anything beginning with `_` on the way in, and inject
the channel id read back from the API rather than hardcoding it.

⚠ **NEVER HARDCODE HOW MANY POLICIES THERE ARE.** An earlier version of this section ended in
`for i in 0 1` over a generator that writes one payload per declared policy. The file later grew
to three, so index 2 was generated and never sent, and
`fdp freshness sentinel itself stopped` sat undeployed — the one policy whose absence is
invisible, because it is the thing that watches the watcher. Found 2026-08-11, GitLab #61.
`tests/test_alert_policy_recipe.py` now fails the build if a literal count reappears here.

The block below is **idempotent**: it reads what already exists, `PATCH`es a policy whose
`displayName` matches, and `POST`s only what is genuinely new. Re-running it is safe, which is
what makes it usable as a repair step rather than a one-shot. It also does the whole job in one
Python process over `urllib`, so there are no payload files on disk and the Windows `curl`
path trap below does not apply to it.

```bash
TOKEN=$(gcloud auth print-access-token) python - <<'EOF'
import json, os, urllib.request

BASE = "https://monitoring.googleapis.com/v3/projects/football-data-pipeline-gcp"
HDRS = {"Authorization": "Bearer " + os.environ["TOKEN"],
        "Content-Type": "application/json"}

def api(path, data=None, method=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers=HDRS, method=method)
    with urllib.request.urlopen(req) as r:
        body = r.read().decode()
    return json.loads(body) if body.strip() else {}

def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o

chans = api("/notificationChannels").get("notificationChannels", [])
assert len(chans) == 1, "expected exactly 1 notification channel, found %d" % len(chans)

existing = {p["displayName"]: p for p in api("/alertPolicies").get("alertPolicies", [])}

# Derived from the file, never from a literal count.
for pol in strip(json.load(open("deploy/nightly/alert-policy.json")))["policies"]:
    pol["notificationChannels"] = [chans[0]["name"]]
    name = pol["displayName"]
    if name in existing:
        pol["name"] = existing[name]["name"]
        api("/" + pol["name"].split("/", 2)[2], data=pol, method="PATCH")
        print("updated", name)
    else:
        api("/alertPolicies", data=pol)
        print("created", name)
EOF
```

It prints one line per declared policy, so the output length is the check: if the file declares
three and you see two lines, something was skipped.

⚠ **The notification-channel creation step above is still a bare `POST` and is NOT idempotent** —
running it twice creates a second channel, and you then get every alert twice, which is how
people learn to ignore alerts. Check before re-running:

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://monitoring.googleapis.com/v3/projects/football-data-pipeline-gcp/notificationChannels" \
  | python -c "import sys,json;[print(c['name'],c.get('type')) for c in json.load(sys.stdin).get('notificationChannels',[])]"
```

To remove a duplicate policy or channel, `DELETE` its `name`.

### Checking and silencing it

```bash
# does the policy exist, is it enabled, is the channel verified
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://monitoring.googleapis.com/v3/projects/football-data-pipeline-gcp/alertPolicies"

# open incidents
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://monitoring.googleapis.com/v3/projects/football-data-pipeline-gcp/alertPolicies?filter=display_name=\"fdp raw data is STALE or uncheckable\""
```

To silence during planned work, PATCH the policy with `"enabled": false` — and re-enable it.
A permanently-disabled alert is the same blind spot this stage exists to close.

**A policy that has never fired is decoration.** The cheap way to prove it works: disable the
Cloud Scheduler job for a day and confirm the email arrives — or temporarily PATCH the absence
`duration` down to `3600s`, wait an hour past the last success, and confirm, then restore
`108000s`.

## Operating it

```bash
# run now, and wait for it (a real prod ingest + dbt build)
gcloud run jobs execute fdp-nightly --region europe-west1 --wait

# what happened
gcloud run jobs executions list --job fdp-nightly --region europe-west1 --limit 5
gcloud beta run jobs executions logs read <EXECUTION> --region europe-west1

# is the schedule healthy
gcloud scheduler jobs describe fdp-nightly --location europe-west1
```

**Confirming a run actually landed data** — the same check that exposed the original six-day
outage, and the one to trust over a green tick:

```bash
bq show --format=prettyjson football-data-pipeline-gcp:raw.RAW_APIF_FIXTURES_NEXT \
  | python -c "import sys,json,datetime;d=json.load(sys.stdin);print(datetime.datetime.utcfromtimestamp(int(d['lastModifiedTime'])/1000))"
```

A run that reports `new_data=false` exits 0 before `dbt deps`, the contract checks, `dbt seed`
and `dbt build`, and writes nothing. **That is a $0 night, not a failure** — the gate is in
`entrypoint.sh` and mirrors the CI job.

**Stage 2 did not change this.** An earlier draft moved `dbt deps` and `dbt source freshness`
above the gate, which would have made a quiet night cost a few cents; that was reverted when
the CPO chose the out-of-band sentinel instead. The nightly is untouched by Stage 2, and
"succeeding but stale" is caught by `fdp-freshness` reading table metadata hourly — outside the
nightly entirely, which is the point.

## Rolling back

The GitLab job is untouched, so rollback is: un-pause the GitLab schedule, and pause or delete
the Cloud Scheduler job.

```bash
gcloud scheduler jobs pause fdp-nightly --location europe-west1
```

## After a code change

**As of GitLab #74, `build:nightly-image` + `deploy:nightly-image` in `.gitlab-ci.yml` rebuild
and redeploy the image automatically** on a push to `main` that touches a path the image
actually contains (`*data_paths_image`) — see "Deploy the job" above for what that covers and
what it does not (the sentinel is still pinned separately). The command above is the manual
fallback now, not
the normal path to prod.

---

## The site deploy (`fdp-site`)

The nightly site deploy is a second Cloud Run job, `fdp-site`. A third Cloud Scheduler entry starts it
after `fdp-nightly` (04:00 UTC, usually done by 05:40). It runs `scripts/nightly_site_deploy.py` in the
image of `deploy/site/Dockerfile`. Its steps:

1. **Guard.** Today's `fdp-nightly` execution must have succeeded. A running one is waited for, up to 45 minutes.
2. **Export.** `export_site_data.py --entities deploy` writes every entity the pages read. It reads marts and seeds only.
3. **Count floor.** `team`, `fixture`, `competition`, `player` and `player_peers` must stay at 90 percent or more of the live counts.
   The live counts are the file the previous deploy published at
   `https://football-data-pipeline-gcp.web.app/export-manifest.json`. A 404 stops the job unless the execution sets `ALLOW_FIRST_DEPLOY=1`.
   Set it for the first deploy, and after a manual deploy, which publishes no counts file. Any other fetch error stops the job.
4. **Crests.** `scripts/sync_crests.py` copies the crest bucket into `site_v2/public/crests/`. A bucket that does not exist yet
   gives a warning and no files. Any other error stops the job.
5. **Build and gates.** The export replaces the committed sample, then `npm run build` runs at an 8 GB heap.
   That is the prebuild tests, `astro build`, `audit-seo` and `check-built-pages`. On a full export the check fails when a crest
   path on a page is no file under `dist/`.
6. **Deploy.** The counts file goes into `dist/`, then `firebase deploy --only hosting` runs.
   A red gate stops the job before this step, so the live site keeps the previous build.

The Cloud Run disk is memory. The export (about 3 GB, moved into the build folder, not copied) and `dist` (about 13 GB) live in it.
The build heap adds up to 8 GB. That is why the job is sized 8 vCPU and 32 GiB. MR builds still read the committed sample.

### Create it, in this order

The image does not exist until the merge that adds this job has pushed `main`. Then `build:site-image` builds it.
`deploy:site-image` fails, because the job does not exist yet. Take the tag from that build (the merge commit).
After the job exists, run `deploy:site-image` again.

```bash
gcloud run jobs create fdp-site \
  --image europe-west1-docker.pkg.dev/football-data-pipeline-gcp/cloud-run-source-deploy/fdp-site:<merge-commit-sha> \
  --region europe-west1 \
  --service-account github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com \
  --cpu 8 --memory 32Gi \
  --task-timeout 3h \
  --max-retries 0
```

`--max-retries 0` makes a failed night a visible red run. The next scheduled run is the retry.
The job runs as the account CI already uses for the warehouse read, the nightly's execution list and the Firebase deploy.
The CI repoint needs one job-scoped grant, so `deploy:site-image` can update `fdp-site` and nothing else:

```bash
gcloud run jobs add-iam-policy-binding fdp-site \
  --region europe-west1 \
  --member="serviceAccount:github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com" \
  --role="roles/run.developer"
```

From here on, `deploy:site-image` repoints the job at every new image. It fails on any error, so a stale image never hides behind a green pipeline.
A first run that fails on another permission names the missing role.

### Keep five images (once)

Every push to `main` that changes what the image carries adds one image of about 1 GB. The repository also holds the nightly image.
The policy applies to the `fdp-site` package only:

```bash
gcloud artifacts repositories list-cleanup-policies cloud-run-source-deploy --location europe-west1
gcloud artifacts repositories set-cleanup-policies cloud-run-source-deploy \
  --location europe-west1 \
  --policy deploy/site/cleanup-policy.json \
  --no-dry-run
```

`set-cleanup-policies` replaces the repository's policies, so read the list first and merge any it shows into the file.

### Cap the release history (once, before the first run)

Every release is about 13 GB. Firebase bills stored releases beyond 10 GB. Keep a few:

```bash
curl -s -X PATCH \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"maxVersions": "3"}' \
  "https://firebasehosting.googleapis.com/v1beta1/projects/football-data-pipeline-gcp/sites/football-data-pipeline-gcp/config?updateMask=maxVersions"
```

### The first run, before any schedule

```bash
gcloud run jobs execute fdp-site --region europe-west1 --update-env-vars ALLOW_FIRST_DEPLOY=1 --wait
```

This deploys live data to the `.web.app` site. The flag lets the first deploy pass, because the live site has no counts file yet.
It is set for this execution only; the job keeps no value of it.
The merge request carries the cost measured on a full local run of the same image, before the merge.
Read these off this run to confirm it, and correct the merge request if they differ:

- **BigQuery bytes** of the export, from the run's time window:

  ```sql
  SELECT COUNT(*) AS queries, ROUND(SUM(total_bytes_billed) / POW(1024, 3), 2) AS gib_billed
  FROM `region-eu`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
  WHERE creation_time BETWEEN TIMESTAMP('<run start>') AND TIMESTAMP('<run end>')
    AND user_email = 'github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com'
    AND job_type = 'QUERY'
  ```

- **Minutes** per step: the job's log prints each step's seconds and the size of `dist`.
- **Peak memory**: `run.googleapis.com/container/memory/utilizations` in Cloud Monitoring.
- **Firebase upload size**: the deploy's own output, and the release list in the Hosting console.

### Schedule it, only after the first run has succeeded

```bash
gcloud run jobs add-iam-policy-binding fdp-site \
  --region europe-west1 \
  --member="serviceAccount:github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud scheduler jobs create http fdp-site \
  --location europe-west1 \
  --schedule "30 6 * * *" \
  --time-zone UTC \
  --uri "https://run.googleapis.com/v2/projects/football-data-pipeline-gcp/locations/europe-west1/jobs/fdp-site:run" \
  --http-method POST \
  --oauth-service-account-email github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com
```

06:30 leaves about 50 minutes after the nightly's usual end. A late nightly is waited for. A failed one stops the deploy.
The GitLab schedule `4379625` stays disabled. The alert policy `fdp-site execution failed` is in `alert-policy.json`.
It goes in with the recipe of "Create the alert policies".

### Stop it, or roll back

```bash
gcloud scheduler jobs pause fdp-site --location europe-west1
```

Roll a bad deploy back in the Firebase console: Hosting, release history, Rollback on the previous release.
The manual `deploy:export` and `deploy:site-v2` jobs in `.gitlab-ci.yml` stay as the fallback by web dispatch.
They publish no counts file, so the next run of `fdp-site` after one needs `--update-env-vars ALLOW_FIRST_DEPLOY=1`.

---

## The crest bucket

Team crests and league logos come from our own domain. The ingest stores them. The site build serves them.

| | |
|---|---|
| Bucket | `gs://football-data-pipeline-gcp-crests`, `europe-west1`, private |
| Objects | `teams/{id}-48.webp`, `teams/{id}-104.webp`, `leagues/{id}-48.webp`, `leagues/{id}-104.webp` |
| State table | `raw.RAW_APIF_CREST_OBJECTS`, one row per run that fetched or checked an image |
| Written by | the crest phase of `python -m ingestion.api_football.main`, inside `fdp-nightly` |
| Read by | `scripts/sync_crests.py`, step 4 of `fdp-site`, which copies it into `site_v2/public/crests/` |
| Served at | `/crests/{teams|leagues}/{id}-104.webp` on our own domain, with a 7-day browser cache (`site_v2/firebase.json`) |

### Create the state table, once, before the merge

The data build reads `RAW_APIF_CREST_OBJECTS` as a source, so the table must exist before the merge. The command creates it empty. It uses the ingest's own table helper and changes nothing when the table exists.

```bash
PYTHONPATH=. python -c "from google.cloud import bigquery; from ingestion.api_football.bigquery import ensure_raw_table_partitioned; ensure_raw_table_partitioned(bigquery.Client(project='football-data-pipeline-gcp'), 'RAW_APIF_CREST_OBJECTS')"
```

The table has two columns, `payload` (JSON) and `ingested_at` (TIMESTAMP), partitioned by day on `ingested_at`. The crest phase creates the same table when it runs.

### Create the bucket, once, before the first nightly after the merge

The CPO runs two commands. The nightly service account writes to the bucket. The site job reads from it. One grant serves both.

```bash
gcloud storage buckets create gs://football-data-pipeline-gcp-crests --project=football-data-pipeline-gcp --location=europe-west1 --default-storage-class=STANDARD --uniform-bucket-level-access --public-access-prevention

gcloud storage buckets add-iam-policy-binding gs://football-data-pipeline-gcp-crests --member=serviceAccount:github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com --role=roles/storage.objectUser
```

Before the bucket exists, the crest phase logs it and writes nothing. The dimensions publish no crest path. The pages show initials.

### What the first nightly does

1. **Pre-flight.** The phase reads the account counter with `GET /status`. That call does not count against the quota.
   It fetches 10 images and reads the counter again. The result, `images_count_quota`, stays in the state. The pre-flight runs once.
2. **Fill.** It fetches every image that has no state, about 3,300 in all. It waits 0.34 seconds between images. It stops on the first 403 or 429.
   If image requests count against the quota, each run fetches at most the requests left today minus 1,000.
3. **Shrink.** Each image becomes two WebP files, fitted inside 48 px and 104 px. Transparency stays.
4. **Check for a change.** Each night, images not checked for 7 days are fetched again, about 475 a night. Their SHA-256 is compared with the state.
   A changed badge is shrunk and written again. The provider's address does not change with the badge, so content is the only signal.

Then `dbt build` publishes the paths. The next `fdp-site` run copies the files and deploys them.

### Look at it

```bash
gcloud storage ls gs://football-data-pipeline-gcp-crests/teams/ | wc -l
bq query --use_legacy_sql=false 'select json_value(payload, "$.preflight.images_count_quota") as images_count_quota, array_length(json_query_array(payload, "$.objects")) as objects, ingested_at from `football-data-pipeline-gcp.raw.RAW_APIF_CREST_OBJECTS` order by ingested_at desc limit 1'
```

### Roll back

Remove the bucket binding or the bucket. The next ingest logs that the bucket is missing. The next `dbt build` publishes no paths. The pages show initials.
