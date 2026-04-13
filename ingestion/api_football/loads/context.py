"""Mutable run context shared across load steps."""

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
