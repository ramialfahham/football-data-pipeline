# Task contract — pin requirements.txt, drop dead deps (#425)

> Audit F20: root requirements.txt leaves several deps unpinned (supply-chain /
> reproducibility drift). CPO ruling 2026-06-12: file. CPO scope ruling 2026-06-13:
> "Pin + remove dead" — pin used deps, drop the unused/misplaced ones.
> See docs/working_agreement.md §2/§10.

objective: >
  Harden the root requirements.txt against supply-chain / reproducibility drift
  (audit F20). Investigation this session (grep across all .py, no .venv):
  - `requests` — USED (http_client, scripts/diagnostics, scripts/squad_watch) → pin
    to the installed/tested version 2.33.1.
  - `beautifulsoup4` — ZERO usage anywhere → remove (dead).
  - `pandas` — ZERO usage anywhere (no import, no load_table_from_dataframe / DataFrame)
    → remove (dead; not flagged by F20 but surfaced to the CPO and approved under the
    "remove dead" ruling).
  - `functions-framework` — used ONLY in ingestion/api_football/main.py, where it is
    already declared in ingestion/api_football/requirements.txt → remove the redundant
    root copy (it belongs with the ingestion entrypoint, not at repo root).
refs: #425 (audit F20).

scope_paths:
  - requirements.txt
  - .claude/task/contract.md
  - .claude/active_work.md   # artifact-only: handover write-out at close (amendment A1)

decisions_taken: >
  CPO ruling 2026-06-13 "Pin + remove dead", RECORDED in
  `.claude/task/escalations.log` (entry 2026-06-13, question 1): pin the used dep
  (requests==2.33.1), remove the two unused deps (beautifulsoup4, pandas) and the
  redundant root functions-framework. The pandas removal — NOT named in F20's text —
  was explicitly surfaced to the CPO in the question context and the chosen option's
  description, and approved knowingly (see the log entry). No live import or CI step
  depends on any removed dep: verified by grep across all repo .py (zero hits for
  bs4/pandas; functions-framework only in ingestion/api_football/main.py, which is
  covered by ingestion/api_football/requirements.txt), and confirmed by validate-local
  offline gates (recorded under done_when). No CI workflow installs root +
  ingestion requirements in the same pip invocation, so dropping the root
  functions-framework cannot break the ingestion entrypoint.

decisions_reserved:
  - pyarrow is also fully unpinned but was NOT named by F20 and IS used (transitively by
    the BigQuery Storage path); do NOT pin or touch it here — out of this issue's scope.
    If a reviewer judges it the same defect, STOP and escalate rather than expand scope.
  - The other floor-pinned deps (python-dotenv>=, google-cloud-bigquery-storage>=,
    PyYAML>=, pytest>=) are pre-existing and out of F20's scope — leave untouched.

done_when:
  - requirements.txt: `requests==2.33.1`; no `beautifulsoup4`, no `pandas`, no
    root-level `functions-framework`; every other line unchanged.
  - grep confirms zero live references to the removed deps (already verified:
    beautifulsoup4/pandas unused; functions-framework only in ingestion, still declared
    in ingestion/api_football/requirements.txt).
  - validate-local offline gates green (pip install of the trimmed file resolves; the
    python-ci test suite imports none of the removed deps).
  - reviewers: scope-auditor (always) + cto-reviewer (requirements*.txt) — PASS.

amendments:
  - 2026-06-13: + .claude/active_work.md — authority: standing rule (handover must be
    kept current at task close; active_work.md is commit-exempt but not auto-editable,
    so it is added to scope_paths to write the handover). content: status update marking
    #425 done (PR #438) and #427 next.
