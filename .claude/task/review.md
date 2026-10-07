# Review — design/match-renders-decisions — 2026-10-07

diff_sha256: b8b55bb7926536e211780ff8e707210ecbff0c3d4da34553e5e528074e8ff1c3

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every file in the diff sits inside the contract's scope_paths; no amendment needed.
- Impact map: no ingestion, dbt model, export or site path is touched, so none is required.
- Credentials: no key, token or secret in the patch; the renders carry only public media URLs.
- Decision rights: the metric list, order and Goals-group exception rest on the #166 and #175 lines approved in chat, 2026-10-07; German and Finnish names (#177) and the played-match page set (#174) stay reserved.
- Metric definitions: the window rule and the one changed number (Bremen's dribbles-completed share, 49 not 47) are declared in decisions_taken.
- Thresholds: no new mechanism, no recurring cost; the one-off 537 MB read is recorded.
- Frontend logic and doc sync: nothing added to site_v2; the edited generator comment matches the new row set.

## escalations
(none)
