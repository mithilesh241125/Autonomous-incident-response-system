from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings grouped in one place for easy changes."""

    api_url: str = os.getenv("AIRS_API_URL", "https://httpbin.org/status/200")
    log_file: str = os.getenv("AIRS_LOG_FILE", "logs.txt")
    database_path: str = os.getenv("AIRS_DB_PATH", "airs.db")
    monitor_interval_seconds: int = int(os.getenv("AIRS_MONITOR_INTERVAL", "5"))
    cpu_high_threshold: int = int(os.getenv("AIRS_CPU_HIGH_THRESHOLD", "85"))
    failure_window_seconds: int = int(os.getenv("AIRS_FAILURE_WINDOW", "60"))
    failure_threshold: int = int(os.getenv("AIRS_FAILURE_THRESHOLD", "3"))
    incident_dedupe_seconds: int = int(os.getenv("AIRS_INCIDENT_DEDUPE", "30"))
    dashboard_limit: int = int(os.getenv("AIRS_DASHBOARD_LIMIT", "20"))


settings = Settings()
