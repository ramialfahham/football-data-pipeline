"""API-Football ingestion package (modular loaders + one orchestrated pipeline)."""

from .pipeline import _load_api_football

__all__ = ["_load_api_football"]
