from __future__ import annotations

import unittest
from pathlib import Path

from analyzer import LogAnalyzer


class LogAnalyzerTests(unittest.TestCase):
    def test_analyze_logs_returns_structured_findings(self) -> None:
        log_path = Path("test_logs.txt")
        self.addCleanup(lambda: log_path.exists() and log_path.unlink())
        log_path.write_text(
            "\n".join(
                [
                    "2026-04-20 ERROR Connection failed while reaching database",
                    "2026-04-20 WARNING Request timeout for billing service",
                ]
            ),
            encoding="utf-8",
        )

        analyzer = LogAnalyzer(str(log_path))
        findings = analyzer.analyze_logs()

        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["error"], "DB connection failed")
        self.assertEqual(findings[1]["severity"], "MEDIUM")


if __name__ == "__main__":
    unittest.main()
