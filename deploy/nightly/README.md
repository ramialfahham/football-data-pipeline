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

## Monitoring — #39 Stage 2

**Why this is out-of-band.** Every check inside the nightly only runs when the nightly runs.
The failure that cost six days of stale data was the nightly **not running at all**, and no
in-pipeline test can ever see that.

**What is monitored is DATA AGE, not job success.** `scripts/check_raw_freshness.py` runs
hourly as its own Cloud Run Job, reads each raw table's last-modified time, and exits non-zero
when it is past the `error_after` already declared in `sources.yml`. Job success is only a
proxy — a pipeline that "succeeds" nightly while writing nothing is stale and would pass a
job-success check. Table age is the real signal.

Three policies, all wired to the same email:

| Policy | Fires when | Means |
|---|---|---|
| `fdp raw data is STALE or uncheckable` | the sentinel exits non-zero | **stale data (exit 1) OR we cannot tell (exit 2)** — read the log |
| `fdp freshness sentinel itself stopped` | no successful sentinel run in 3h | we can no longer *tell* |
| `fdp-nightly execution failed` | a nightly run dies | early warning, before staleness |

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
nightly's image, so that image must already contain `scripts/check_raw_freshness.py`. Until
Stage 3 has CI rebuild the image on merge, the sequence is:

1. merge the branch that adds the script
2. rebuild: `gcloud run jobs deploy fdp-nightly --source . --region europe-west1` (from `main`)
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

`alert-policy.json` holds BOTH policies under `policies`, plus `_comment` keys for the reader.
The API rejects unknown fields, so strip anything beginning with `_` on the way in, and inject
the channel id read back from the API rather than hardcoding it:

```bash
CHANNEL=$(curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://monitoring.googleapis.com/v3/projects/football-data-pipeline-gcp/notificationChannels" \
  | python -c "import sys,json;print(json.load(sys.stdin)['notificationChannels'][0]['name'])")

python -c "
import json
def strip(o):
    if isinstance(o,dict):  return {k:strip(v) for k,v in o.items() if not k.startswith('_')}
    if isinstance(o,list):  return [strip(v) for v in o]
    return o
for i,p in enumerate(strip(json.load(open('deploy/nightly/alert-policy.json')))['policies']):
    p['notificationChannels'] = ['$CHANNEL']
    json.dump(p, open('pol%d.json' % i, 'w'))
"

for i in 0 1; do
  curl -s -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    "https://monitoring.googleapis.com/v3/projects/football-data-pipeline-gcp/alertPolicies" \
    -d @pol$i.json
done
rm -f pol0.json pol1.json
```

⚠ **`curl` on Windows cannot read a Git Bash `/tmp/...` path** — write the payloads to a
Windows-visible directory or the repo root, as above. `-d @/tmp/x.json` fails with
*"option -d: error encountered when reading a file"*.

⚠ **NEITHER command is idempotent.** Both are bare `POST`s with no existence check, so running
this section twice creates a *second* notification channel and a *second* pair of policies —
and you then get every alert twice, which is how people learn to ignore alerts. Check before
re-running:

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://monitoring.googleapis.com/v3/projects/football-data-pipeline-gcp/alertPolicies" \
  | python -c "import sys,json;[print(p['name'],p['displayName']) for p in json.load(sys.stdin).get('alertPolicies',[])]"
```

To change an existing policy, `PATCH` its `name` rather than re-POSTing. To remove a duplicate,
`DELETE` that `name`.

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

The image is **not** rebuilt automatically — Stage 3 wires that into CI on merge. Until then,
re-run the `gcloud run jobs deploy` command above after merging anything that changes
ingestion, the dbt project, or `requirements.txt`.

This is a real gap, stated rather than hidden: between a merge and a redeploy, the nightly runs
the previous image.
