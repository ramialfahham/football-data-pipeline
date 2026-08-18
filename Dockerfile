# The nightly pipeline image. GitLab #39 Stage 1.
#
# Built by CI (`build:nightly-image` in .gitlab-ci.yml) with kaniko — no Cloud Build, no
# privileged Docker, no local Docker needed. GitLab #74: `gcloud run jobs deploy --source .`
# (which needs Cloud Build) is the documented manual fallback only — see
# deploy/nightly/README.md "Deploy the job".
#
# WHY AN IMAGE AT ALL, rather than pointing a scheduler at the repo: today the nightly
# pip-installs at 04:00 and runs whatever `main` happens to be, so what executes in production
# is never the thing that was tested. An image is built once and re-run byte-identical.

FROM python:3.11-slim

# git: `dbt deps` fetches packages from git remotes (see dbt_project/packages.yml).
# Nothing else is added — the smaller the surface, the less there is to patch.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first, as their own layer: requirements.txt changes far less often than the
# source, so ordinary code changes reuse the cached install.
#
# This is the SAME requirements.txt CI installs. Stage 1 adds no dependency — if these ever
# diverge, the image stops being a faithful stand-in for the tested environment.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# dbt reads ~/.dbt/profiles.yml by default. Prod target only — see the file's own header.
RUN mkdir -p /root/.dbt && cp deploy/nightly/profiles.yml /root/.dbt/profiles.yml

RUN chmod +x deploy/nightly/entrypoint.sh

# Unbuffered, so Cloud Logging shows progress live rather than in one dump at the end. The
# 2026-08-09 outage was diagnosed by reading a running job's log; that has to keep working.
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["deploy/nightly/entrypoint.sh"]
