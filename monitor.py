from __future__ import annotations

import random
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from analyzer import LogAnalyzer
from config import Settings
from detector import IncidentDetector
from healer import AutoHealer, build_alert
from storage import SQLiteStorage


class MonitoringService:
    """Runs the Monitor -> Detect -> Analyze -> Decide -> Fix -> Notify loop."""

    def __init__(self, repository: SQLiteStorage, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings
        self.detector = IncidentDetector(
            window_seconds=self.settings.failure_window_seconds,
            failure_threshold=self.settings.failure_threshold,
        )
        self.analyzer = LogAnalyzer(self.settings.log_file)
        self.healer = AutoHealer()
        self.interval_seconds = self.settings.monitor_interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the background monitoring thread once."""
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background loop when shutting down."""
        self._stop_event.set()

    def _run_loop(self) -> None:
        """Repeatedly check health, detect incidents, analyze logs, and heal issues."""
        while not self._stop_event.is_set():
            snapshot = self.collect_health()
            self.repository.save_health(snapshot)

            incidents = self.detector.detect(snapshot)
            log_findings = self.analyzer.analyze_logs()
            new_log_findings = self.repository.record_log_analysis(log_findings)
            log_incidents = self._log_findings_to_incidents(new_log_findings)

            for incident in incidents + log_incidents:
                incident["fingerprint"] = self._build_fingerprint(incident)
                incident_id = self.repository.create_incident(
                    incident,
                    dedupe_seconds=self.settings.incident_dedupe_seconds,
                )
                if incident_id is None:
                    continue

                action = self.healer.heal(incident)
                self.repository.record_action(incident_id, action)
                self.repository.resolve_incident(incident_id, action["action"])
                self.repository.record_alert(incident_id, build_alert(incident, action))
            time.sleep(self.interval_seconds)

    def collect_health(self) -> Dict[str, object]:
        """Gather the current health view used by the detector."""
        api_status = self.check_api_status(self.settings.api_url)
        cpu_usage = self.get_cpu_usage()
        simulated_anomaly = random.choice([False, False, False, True])

        return {
            "api_status": api_status,
            "cpu_usage": cpu_usage,
            "simulated_anomaly": simulated_anomaly,
            "status": "UP" if api_status == 200 and cpu_usage < self.settings.cpu_high_threshold else "DOWN",
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    @staticmethod
    def get_cpu_usage() -> int:
        """Return a fake CPU percentage so the demo works anywhere."""
        return random.randint(20, 95)

    @staticmethod
    def check_api_status(url: str = "https://httpbin.org/status/200") -> int:
        """Call a test endpoint and sometimes simulate a failure for demo purposes."""
        if random.choice([False, False, True]):
            return 500

        request = Request(url, headers={"User-Agent": "AutonomousIncidentResponseSystem/1.0"})
        try:
            with urlopen(request, timeout=2) as response:
                return int(response.status)
        except URLError:
            return 500

    def _log_findings_to_incidents(self, findings: List[Dict[str, str]]) -> List[Dict[str, object]]:
        """Convert analyzer results into a detector-like incident format."""
        incidents: List[Dict[str, object]] = []
        for finding in findings:
            error = finding["error"]
            incident_type = self._incident_type_for_finding(error)
            incidents.append(
                {
                    "type": incident_type,
                    "message": f"{error} detected from logs.",
                    "severity": finding["severity"],
                    "status": "OPEN",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "log_line": finding["log_line"],
                    "cause": finding["cause"],
                    "fingerprint": f"{incident_type}:{finding['log_line']}",
                }
            )
        return incidents

    def _incident_type_for_finding(self, error: str) -> str:
        """Map analyzer findings to specific incident types for smarter healing."""
        mapping = {
            "DB connection failed": "DB_CONNECTION",
            "Service timeout": "TIMEOUT",
            "Memory error": "MEMORY_ERROR",
        }
        return mapping.get(error, "LOG_PATTERN")

    @staticmethod
    def _build_fingerprint(incident: Dict[str, object]) -> str:
        """Create a stable deduplication key for the incident."""
        log_line = str(incident.get("log_line", ""))
        if log_line:
            return f"{incident['type']}:{log_line}"
        return f"{incident['type']}:{incident['message']}"
