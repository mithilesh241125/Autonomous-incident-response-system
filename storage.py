from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class SQLiteStorage:
    """SQLite-backed persistence layer for incidents, actions, alerts, and health."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Create the tables used by the dashboard if they do not exist yet."""
        with self._lock:
            cursor = self._connection.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS health_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_status INTEGER,
                    cpu_usage INTEGER,
                    simulated_anomaly INTEGER,
                    status TEXT,
                    checked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT NOT NULL,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    resolved_at TEXT,
                    log_line TEXT,
                    cause TEXT,
                    action_taken TEXT
                );

                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id INTEGER,
                    incident_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id INTEGER,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS log_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error TEXT NOT NULL,
                    cause TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    log_line TEXT NOT NULL UNIQUE,
                    detected_at TEXT NOT NULL
                );
                """
            )
            self._connection.commit()

    def close(self) -> None:
        """Close the SQLite connection when the process exits."""
        with self._lock:
            self._connection.close()

    def save_health(self, snapshot: Dict[str, object]) -> None:
        """Persist the latest health check."""
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO health_snapshots (api_status, cpu_usage, simulated_anomaly, status, checked_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot["api_status"],
                    snapshot["cpu_usage"],
                    int(bool(snapshot["simulated_anomaly"])),
                    snapshot["status"],
                    snapshot["checked_at"],
                ),
            )
            self._connection.commit()

    def get_latest_health(self) -> Optional[Dict[str, object]]:
        """Return the most recent health snapshot."""
        with self._lock:
            row = self._connection.execute(
                """
                SELECT api_status, cpu_usage, simulated_anomaly, status, checked_at
                FROM health_snapshots
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        return {
            "api_status": row["api_status"],
            "cpu_usage": row["cpu_usage"],
            "simulated_anomaly": bool(row["simulated_anomaly"]),
            "status": row["status"],
            "checked_at": row["checked_at"],
        }

    def record_log_analysis(self, findings: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Store new log analysis records and return only the unseen findings."""
        detected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_findings: List[Dict[str, str]] = []

        with self._lock:
            for finding in findings:
                cursor = self._connection.execute(
                    """
                    INSERT OR IGNORE INTO log_analysis (error, cause, severity, log_line, detected_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        finding["error"],
                        finding["cause"],
                        finding["severity"],
                        finding["log_line"],
                        detected_at,
                    ),
                )
                if cursor.rowcount == 1:
                    new_findings.append(finding)
            self._connection.commit()

        return new_findings

    def list_log_analysis(self, limit: int) -> List[Dict[str, str]]:
        """Return recent log analysis results for the dashboard."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT error, cause, severity, log_line, detected_at
                FROM log_analysis
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def create_incident(self, incident: Dict[str, object], dedupe_seconds: int) -> Optional[int]:
        """Insert a new incident unless the same fingerprint happened too recently."""
        fingerprint = str(incident["fingerprint"])
        now = datetime.now()
        now_text = now.strftime("%Y-%m-%d %H:%M:%S")
        dedupe_cutoff = (now - timedelta(seconds=dedupe_seconds)).strftime("%Y-%m-%d %H:%M:%S")
        created_at = str(incident.get("timestamp", now_text))

        with self._lock:
            existing = self._connection.execute(
                """
                SELECT id
                FROM incidents
                WHERE fingerprint = ?
                  AND updated_at >= ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (fingerprint, dedupe_cutoff),
            ).fetchone()
            if existing is not None:
                return None

            cursor = self._connection.execute(
                """
                INSERT INTO incidents
                (fingerprint, type, message, severity, status, created_at, updated_at, resolved_at, log_line, cause, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fingerprint,
                    incident["type"],
                    incident["message"],
                    incident["severity"],
                    incident.get("status", "OPEN"),
                    created_at,
                    now_text,
                    None,
                    incident.get("log_line"),
                    incident.get("cause"),
                    None,
                ),
            )
            self._connection.commit()
            return int(cursor.lastrowid)

    def resolve_incident(self, incident_id: int, action_taken: str) -> None:
        """Mark an incident as resolved after self-healing succeeds."""
        resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._connection.execute(
                """
                UPDATE incidents
                SET status = ?, updated_at = ?, resolved_at = ?, action_taken = ?
                WHERE id = ?
                """,
                ("RESOLVED", resolved_at, resolved_at, action_taken, incident_id),
            )
            self._connection.commit()

    def record_action(self, incident_id: Optional[int], action: Dict[str, str]) -> None:
        """Store a healing action."""
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO actions (incident_id, incident_type, action, status, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    action["incident_type"],
                    action["action"],
                    action.get("status", "COMPLETED"),
                    action["timestamp"],
                ),
            )
            self._connection.commit()

    def record_alert(self, incident_id: Optional[int], message: str) -> None:
        """Store a user-facing alert."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO alerts (incident_id, message, timestamp)
                VALUES (?, ?, ?)
                """,
                (incident_id, message, timestamp),
            )
            self._connection.commit()

    def list_incidents(self, limit: int) -> List[Dict[str, object]]:
        """Return recent incidents."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT id, type, message, severity, status, created_at, updated_at, resolved_at, log_line, cause, action_taken
                FROM incidents
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        incidents: List[Dict[str, object]] = []
        for row in rows:
            incidents.append(
                {
                    "id": row["id"],
                    "type": row["type"],
                    "message": row["message"],
                    "severity": row["severity"],
                    "status": row["status"],
                    "timestamp": row["created_at"],
                    "updated_at": row["updated_at"],
                    "resolved_at": row["resolved_at"],
                    "log_line": row["log_line"],
                    "cause": row["cause"],
                    "action_taken": row["action_taken"],
                }
            )
        return incidents

    def list_actions(self, limit: int) -> List[Dict[str, object]]:
        """Return recent healing actions."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT incident_id, incident_type, action, status, timestamp
                FROM actions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def list_alerts(self, limit: int) -> List[Dict[str, object]]:
        """Return recent alerts."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT incident_id, message, timestamp
                FROM alerts
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]
