# The nightly site image: export, build and deploy of the Matchday Pilot site (GitLab #156).
#
# Built by CI (`build:site-image` in .gitlab-ci.yml) with kaniko, the same way the nightly image is,
# and run as the Cloud Run job `fdp-site`; deploy/nightly/README.md is the runbook.
#
# Python for the export, Node for the build and Firebase's CLI. `npm ci` is baked in, so a night
# spends no time installing.

FROM node:24-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:${PATH}"

RUN npm install -g firebase-tools@13

WORKDIR /app

# The SAME requirements.txt CI installs.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY site_v2/package.json site_v2/package-lock.json ./site_v2/
RUN npm ci --prefix site_v2

COPY . .

ENV PYTHONPATH=/app
CMD ["python", "scripts/nightly_site_deploy.py"]
