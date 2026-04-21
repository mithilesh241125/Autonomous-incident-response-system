from __future__ import annotations

from pathlib import Path
from typing import Dict, List


# Known log patterns and the root-cause details we want to return.
ERROR_PATTERNS: Dict[str, Dict[str, str]] = {
    "connection failed": {
        "error": "DB connection failed",
        "cause": "Too many connections",
        "severity": "HIGH",
    },
    "timeout": {
        "error": "Service timeout",
        "cause": "Downstream service is slow or unavailable",
        "severity": "MEDIUM",
    },
    "memory error": {
        "error": "Memory error",
        "cause": "Application may be using too much memory",
        "severity": "HIGH",
    },
}


class LogAnalyzer:
    """Reads log lines and converts known patterns into structured incidents."""

    def __init__(self, log_file: str = "logs.txt") -> None:
        self.log_file = Path(log_file)

    def read_logs(self) -> List[str]:
        """Return every line from the log file. Missing file means no logs yet."""
        if not self.log_file.exists():
            return []

        return self.log_file.read_text(encoding="utf-8").splitlines()

    def analyze_logs(self) -> List[Dict[str, str]]:
        """Scan logs for supported error patterns and return root-cause details."""
        findings: List[Dict[str, str]] = []
        for line in self.read_logs():
            lowered = line.lower()
            for pattern, details in ERROR_PATTERNS.items():
                if pattern in lowered:
                    finding = dict(details)
                    finding["log_line"] = line
                    findings.append(finding)
        return findings
