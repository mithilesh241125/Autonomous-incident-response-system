from __future__ import annotations

import unittest

from detector import IncidentDetector


class IncidentDetectorTests(unittest.TestCase):
    def test_detects_api_failure_and_high_cpu(self) -> None:
        detector = IncidentDetector(window_seconds=60, failure_threshold=3)
        incidents = detector.detect(
            {
                "api_status": 500,
                "cpu_usage": 90,
                "simulated_anomaly": False,
            }
        )

        incident_types = {item["type"] for item in incidents}
        self.assertIn("API_FAILURE", incident_types)
        self.assertIn("HIGH_CPU", incident_types)

    def test_detects_high_error_rate_after_multiple_failures(self) -> None:
        detector = IncidentDetector(window_seconds=60, failure_threshold=3)
        payload = {"api_status": 500, "cpu_usage": 30, "simulated_anomaly": False}

        detector.detect(payload)
        detector.detect(payload)
        incidents = detector.detect(payload)

        self.assertTrue(any(item["type"] == "HIGH_ERROR_RATE" for item in incidents))


if __name__ == "__main__":
    unittest.main()
