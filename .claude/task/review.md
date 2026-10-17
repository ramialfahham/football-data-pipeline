# Review — fix/156-deploy-exports-every-page-input — 2026-10-17

diff_sha256: ce2e8bf8bfcd57474180b617dd5d048ec9a2c065af673d36978c53cb2ab18eb3

rounds: 3

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 3: the README's history pin in test_no_decision_history_in_docs.py drops from 18 to 16, a ratchet tightening; the CI flow is unchanged.
- New mechanism: a find and a cp in deploy:site-v2 and a staging artifact path; no new job, hook, package, service or schedule.
- Guard authority: protected_override names both deploy jobs, scoped to scripts, artifact path and comments, with a real impact_map; the hunks touch only those.
- Fail closed: both jobs keep their rules and needs; a failed export, find or cp stops the job before npm ci and Firebase.
- Cost: 0.370 GiB per manual deploy, declared as a THRESHOLD with its approval; no trigger or schedule added.
- Entity list covers every src/data reader in site_v2; the emptying removes nothing the build needs.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 3: the MR pipeline failed on the README's history pin; it drops from 18 to 16, and the full suite passes (1548 passed, 2 skipped).
- Round 1 failed the emptying in deploy:export, which the build job's own checkout undid; round 2 empties in deploy:site-v2 after the artifact lands, so the build sees export-only data, as the local proof modelled.
- The find path is relative to the job's clone, keeps the folder and README.md, and fails the job closed on error; a re-run starts from a fresh clone.
- The staging folder is read by nothing in site_v2; manifest.json and slug_map.json reach src/data through the copy.
- Timeouts: the export took about 16 min of 1h; the build 880s of 1h; the copy adds seconds to minutes.
- The CPO ruled out a test pinning the CI script; a dropped entity fails the build, and a dropped find is caught by the audit and the page-count check.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 3: only the history pin changes (18 to 16), following the README deletions; no display surface.
- Round 1 failed three README claims the change made false; all three are deleted.
- The README opening matches the two jobs; no later paragraph contradicts it.
- The entity list covers every data set read under site_v2/src and site_v2/scripts; nothing reads players, nav, leaderboards or metrics.json.
- Binding rule: the sample is emptied before the copy, so no page is built from data the export does not write.
- site_architecture.md and the 08_browse.md removal match the CI file; the sentence-length pin follows the deleted sentence.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3: tests/test_no_decision_history_in_docs.py is in scope with a dated amendment; its one change lowers the README pin.
- Round 1 failed two README claims; both are deleted, with no new wording.
- Every path is in scope_paths; each added path carries a dated amendment with its authority.
- .gitlab-ci.yml hunks sit only in deploy:export and deploy:site-v2; rules and needs unchanged.
- Thresholds declared; the four reserved full-scale defects are untouched; no decision history in code or docs.

## escalations
(none)
