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

A run that reports `new_data=false` exits 0 before dbt and writes nothing. **That is a $0
night, not a failure** — the gate is in `entrypoint.sh` and mirrors the CI job.

## Rolling back

The GitLab job is untouched, so rollback is: un-pause the GitLab schedule, and pause or delete
the Cloud Scheduler job.

```bash
gcloud scheduler jobs pause fdp-nightly --location europe-west1
```

## After a code change

The image is **not** rebuilt automatically — Stage 3 wires that into CI on merge. Until then,
re-run the `gcloud run jobs deploy` command above after merging anything that changes
ingestion, the dbt project, or `requirements.txt`.

This is a real gap, stated rather than hidden: between a merge and a redeploy, the nightly runs
the previous image.
