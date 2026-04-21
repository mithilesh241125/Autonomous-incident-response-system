# Autonomous Incident Response System

This project simulates a small DevOps/SRE backend that monitors system health, detects failures, analyzes logs, decides on corrective actions, applies self-healing, and shows everything on a Flask dashboard.

## Project Structure

- `app.py` starts the Flask application and dashboard.
- `config.py` stores environment-driven settings.
- `monitor.py` runs the background monitoring loop.
- `detector.py` detects failures and creates incidents.
- `analyzer.py` reads `logs.txt` and maps log patterns to causes.
- `healer.py` simulates recovery actions and alert messages.
- `storage.py` persists runtime data in SQLite.
- `templates/dashboard.html` shows health, incidents, logs, and actions.
- `airs.db` is created automatically to save runtime data.

## Features

- Periodic API health checks
- Simulated CPU usage and anomaly detection
- Error-rate detection in a short time window
- Log pattern analysis for:
  - `connection failed`
  - `timeout`
  - `memory error`
- Root cause analysis output with error, cause, and severity
- Simulated self-healing actions:
  - restart service
  - clear cache
  - retry failed request
- Auto-refreshing dashboard
- SQLite persistence for incidents, alerts, actions, health, and RCA output
- Configurable thresholds and intervals through environment variables
- Incident status tracking with deduplication cooldowns
- Built-in unit tests for the core modules

## How To Run

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the Flask app:

   ```bash
   python app.py
   ```

3. Open your browser at:

   ```text
   http://127.0.0.1:5000
   ```

## Notes

- The API health check uses `https://httpbin.org/status/200` and also randomly simulates failures so the dashboard has interesting events to display.
- CPU usage and anomalies are simulated to keep the project simple and beginner-friendly.
- Incidents, alerts, actions, and latest health are stored in `airs.db`.
- You can customize behavior with environment variables like `AIRS_MONITOR_INTERVAL`, `AIRS_CPU_HIGH_THRESHOLD`, `AIRS_FAILURE_THRESHOLD`, and `AIRS_DB_PATH`.

## Run Tests

```bash
python -m unittest discover -s tests
```
