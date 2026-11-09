"""Mutable run context and per-competition result types shared across load steps."""

from __future__ import annotations

from dataclasses import dataclass, field

from google.cloud import bigquery


@dataclass
class PipelineContext:
    client: bigquery.Client
    headers: dict
    errors: list[str] = field(default_factory=list)
    tables_loaded: int = 0
    # "LEAGUE/ENTITY" pairs skipped on purpose by the re-fetch cadence; the completeness gate
    # reads this to tell a skip from a gap.
    skipped_per_team: set[str] = field(default_factory=set)

    def add_loaded(self, n: int = 1) -> None:
        self.tables_loaded += n

    def record_skipped(self, league_code: str, entity: str) -> None:
        self.skipped_per_team.add(f"{league_code}/{entity}")


@dataclass
class CompetitionRunResult:
    """Output of run_cheap_phases() and run_poll_phases(), consumed by the global fanout."""

    league_code: str
    seasons_list: list[int]
    fixtures_merged: dict
    fixture_ids: set[int]
    team_ids: set[int]
    cov: dict[str, bool]
