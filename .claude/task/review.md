# Review — docs/readme-current — README states only what is true today

diff_sha256: d715502a7f3911db77fb014c75c6c62933b9729bd0760a15ec6f8b5955c6d0bd

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Only README.md and task artifacts change, all in scope_paths; no product, metric, naming or rule change.
- Anchors cited elsewhere ("Getting started", "Secrets", the long-paths text) still exist.
- No file cites a removed README section; every removed copy is still owned by layering.md, profiles.example.yml or agent_guardrails.md.
- Setup, pre-commit, CI, cost and design-decision claims checked against bootstrap.py, .pre-commit-config.yaml, post-commit, .gitlab-ci.yml, check_layer_contract.py, generate_metric_sql.py, 3_core.
- Round 2: "generated from that row" narrowed to "most of them" (83 of 89 catalogue metrics are generated).

## escalations
(none)
