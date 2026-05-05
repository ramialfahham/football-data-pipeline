"""API-Football ingestion package (modular loaders + one orchestrated pipeline)."""

from .orchestrator import _load_api_football

__all__ = ["_load_api_football"]
