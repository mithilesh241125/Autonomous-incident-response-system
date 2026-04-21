from __future__ import annotations

import unittest

from storage import SQLiteStorage


class SQLiteStorageTests(unittest.TestCase):
    def test_log_analysis_only_returns_new_findings_once(self) -> None:
        storage = SQLiteStorage(":memory:")
        finding = {
            "error": "Service timeout",
            "cause": "Downstream service is slow or unavailable",
            "severity": "MEDIUM",
            "log_line": "2026-04-20 timeout",
        }

        first = storage.record_log_analysis([finding])
        second = storage.record_log_analysis([finding])

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)
        storage.close()

    def test_incident_dedup_skips_recent_duplicate(self) -> None:
        storage = SQLiteStorage(":memory:")
        incident = {
            "fingerprint": "API_FAILURE:core-api",
            "type": "API_FAILURE",
            "message": "API returned a non-200 status code.",
            "severity": "HIGH",
            "status": "OPEN",
            "timestamp": "2026-04-20 12:00:00",
        }

        first = storage.create_incident(incident, dedupe_seconds=300)
        second = storage.create_incident(incident, dedupe_seconds=300)

        self.assertIsNotNone(first)
        self.assertIsNone(second)
        storage.close()


if __name__ == "__main__":
    unittest.main()
