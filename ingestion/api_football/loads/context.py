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

    def add_loaded(self, n: int = 1) -> None:
        self.tables_loaded += n


@dataclass
class CompetitionRunResult:
    """Output of run_cheap_phases() — carries all state needed for the global fanout and squads."""

    league_code: str
    seasons_list: list[int]
    fixtures_merged: dict
    fixture_ids: set[int]
    team_ids: set[int]
    cov: dict[str, bool]
