from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List


class IncidentDetector:
    """Turns raw health data into incidents and short-term failure statistics."""

    def __init__(self, window_seconds: int = 60, failure_threshold: int = 3) -> None:
        self.window_seconds = window_seconds
        self.failure_threshold = failure_threshold
        self.failure_history: List[datetime] = []

    def detect(self, health_snapshot: Dict[str, object]) -> List[Dict[str, object]]:
        """Create incidents for anything abnormal in the latest health check."""
        incidents: List[Dict[str, object]] = []
        now = datetime.now()

        if health_snapshot.get("api_status") != 200:
            self.failure_history.append(now)
            incidents.append(
                self._create_incident(
                    "API_FAILURE",
                    "API returned a non-200 status code.",
                    "HIGH",
                )
            )

        if health_snapshot.get("cpu_usage", 0) >= 85:
            incidents.append(
                self._create_incident(
                    "HIGH_CPU",
                    f"CPU usage is high at {health_snapshot['cpu_usage']}%.",
                    "MEDIUM",
                )
            )

        if health_snapshot.get("simulated_anomaly"):
            incidents.append(
                self._create_incident(
                    "SIMULATED_ANOMALY",
                    "A simulated system anomaly was detected.",
                    "MEDIUM",
                )
            )

        recent_cutoff = now - timedelta(seconds=self.window_seconds)
        self.failure_history = [stamp for stamp in self.failure_history if stamp >= recent_cutoff]

        if len(self.failure_history) >= self.failure_threshold:
            incidents.append(
                self._create_incident(
                    "HIGH_ERROR_RATE",
                    "Multiple API failures happened in a short time window.",
                    "HIGH",
                )
            )

        return incidents

    @staticmethod
    def _create_incident(kind: str, message: str, severity: str) -> Dict[str, object]:
        """Return a normalized incident payload with a timestamp."""
        return {
            "type": kind,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resolved": False,
        }
