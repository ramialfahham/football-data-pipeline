"""Mutable run context and per-competition result types shared across load steps."""

from __future__ import annotations

from dataclasses import dataclass, field

from google.cloud import bigquery


@dataclass
class PipelineContext:
    """HTTP + BigQuery client, error sink, and successful raw-table counter for one job run."""

    client: bigquery.Client
    headers: dict
    errors: list[str] = field(default_factory=list)
    tables_loaded: int = 0
    # "LEAGUE/ENTITY" pairs whose phase was deliberately SKIPPED this run by the #33 item 14
    # re-fetch cadence. The completeness gate reads this to tell a skip apart from a gap.
    #
    # WHY IT IS RECORDED HERE RATHER THAN RECOMPUTED: the gate could call `should_refetch` itself,
    # but then two places would decide what "due" means and they would drift. This records what
    # ACTUALLY happened at the call site that made the decision.
    skipped_per_team: set[str] = field(default_factory=set)

    def add_loaded(self, n: int = 1) -> None:
        self.tables_loaded += n

    def record_skipped(self, league_code: str, entity: str) -> None:
        """Note that `entity` was not fetched for `league_code` on this run."""
        self.skipped_per_team.add(f"{league_code}/{entity}")


@dataclass
class CompetitionRunResult:
    """Output of run_cheap_phases() — carries all state needed for the global fanout and squads."""

    league_code: str
    seasons_list: list[int]
    fixtures_merged: dict
    fixture_ids: set[int]
    team_ids: set[int]
    cov: dict[str, bool]
