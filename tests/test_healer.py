from __future__ import annotations

import unittest

from healer import AutoHealer


class AutoHealerTests(unittest.TestCase):
    def test_timeout_incident_retries_request(self) -> None:
        healer = AutoHealer()
        action = healer.heal({"type": "TIMEOUT"})

        self.assertEqual(action["action"], "Failed request retried successfully.")
        self.assertEqual(action["status"], "COMPLETED")

    def test_memory_incident_clears_cache(self) -> None:
        healer = AutoHealer()
        action = healer.heal({"type": "MEMORY_ERROR"})

        self.assertEqual(action["action"], "Cache cleared to reduce load.")


if __name__ == "__main__":
    unittest.main()
