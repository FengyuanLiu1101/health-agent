"""Pluggable read-side access to daily health metrics.

Tools and scoring should prefer this module over calling ``data.db`` directly so
a future wearable API or CSV import can swap in without rewriting the agent.
Writes (simulator, profile, feedback) still go through ``data.db`` for now.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from data import db


@runtime_checkable
class HealthDataSource(Protocol):
    def get_log_by_date(self, iso_date: str) -> Optional[dict]:
        ...

    def get_last_n_logs(self, n: int) -> list[dict]:
        ...


class SqliteHealthDataSource:
    """Default backend: SQLite via ``data.db``."""

    def get_log_by_date(self, iso_date: str) -> Optional[dict]:
        return db.get_log_by_date(iso_date)

    def get_last_n_logs(self, n: int) -> list[dict]:
        return db.get_last_n_logs(n)


_active: HealthDataSource = SqliteHealthDataSource()


def set_health_data_source(source: HealthDataSource) -> None:
    """Replace the global read backend (tests or custom integrations)."""
    global _active
    _active = source


def get_health_data_source() -> HealthDataSource:
    return _active


def get_log_by_date(iso_date: str) -> Optional[dict]:
    return _active.get_log_by_date(iso_date)


def get_last_n_logs(n: int) -> list[dict]:
    return _active.get_last_n_logs(n)
