from __future__ import annotations

from datetime import datetime
from typing import Dict


class AutoHealer:
    """Chooses and simulates a self-healing action for each incident."""

    def __init__(self) -> None:
        self.action_map = {
            "API_FAILURE": self.retry_failed_request,
            "HIGH_ERROR_RATE": self.restart_service,
            "HIGH_CPU": self.clear_cache,
            "SIMULATED_ANOMALY": self.restart_service,
            "DB_CONNECTION": self.restart_service,
            "TIMEOUT": self.retry_failed_request,
            "MEMORY_ERROR": self.clear_cache,
            "LOG_PATTERN": self.clear_cache,
        }

    def heal(self, incident: Dict[str, object]) -> Dict[str, str]:
        """Run the matching healing action and return a structured action record."""
        action = self.action_map.get(str(incident.get("type")), self.retry_failed_request)
        action_message = action()
        return {
            "incident_type": str(incident.get("type")),
            "action": action_message,
            "status": "COMPLETED",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    @staticmethod
    def restart_service() -> str:
        """Simulate restarting a service."""
        return "Service restarted successfully."

    @staticmethod
    def clear_cache() -> str:
        """Simulate cache cleanup."""
        return "Cache cleared to reduce load."

    @staticmethod
    def retry_failed_request() -> str:
        """Simulate retrying a failed request."""
        return "Failed request retried successfully."


def build_alert(incident: Dict[str, object], action: Dict[str, str]) -> str:
    """Create a human-readable alert message for the dashboard."""
    return f"{incident['message']} {action['action']}"
