# Home Lab SIEM Platform

A lightweight Security Information and Event Management (SIEM) platform built in Python, designed for home lab use. Monitor your log files in real time, detect suspicious activity using customizable rules, and view everything through a clean web dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Flask](https://img.shields.io/badge/Flask-3.1-green) ![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

- **Real-time log ingestion** — automatically tails any `.log` or `.txt` file dropped into the watched folder
- **Alert rules engine** — define detection rules using keywords or regular expressions (JSON format, no coding required)
- **8 built-in detection rules** — SSH brute force, root login, port scan, sudo usage, firewall blocks, service crashes, and more
- **Web dashboard** — live stat cards, hourly event timeline chart, severity breakdown, recent alerts, and top sources
- **Events & Alerts pages** — filterable tables with pagination
- **REST API** — JSON endpoints for `/api/stats`, `/api/events`, and `/api/alerts`
- **SQLite storage** — no external database required

---

## Screenshots

> Dashboard with live event and alert data from ingested logs.

| Dashboard | Events | Alerts |
|---|---|---|
| Stat cards, charts, recent alerts | Filterable log event table | All triggered rule matches |

---

## Requirements

- Python 3.10 or higher
- pip (comes with Python)
- Git

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/RobPeeples/SIEM_Platform_Design_v1.git
cd SIEM_Platform_Design_v1
```

### 2. (Optional but recommended) Create a virtual environment

```bash
# Windows
py -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
# Windows
py -m pip install -r requirements.txt

# macOS / Linux
pip install -r requirements.txt
```

---

## Running the SIEM

### Development mode (recommended for home lab use)

```bash
# Windows
py main.py --dev

# macOS / Linux
python main.py --dev
```

Then open your browser and go to: **http://127.0.0.1:5000**

The `--dev` flag enables Flask's auto-reload — any code changes you make will restart the server automatically so you can see them without restarting manually.

### Standard mode

```bash
py main.py        # Windows
python main.py    # macOS / Linux
```

---

## How It Works

```
logs/ folder  →  File Watcher  →  Rules Engine  →  SQLite DB  →  Web Dashboard
```

1. Drop any `.log` or `.txt` file into the `logs/` folder
2. The file watcher detects new lines and sends them to the rules engine
3. The rules engine checks each line against `rules/default_rules.json`
4. Matched lines become **alerts**; all lines become **events**
5. The web dashboard displays everything in real time

A sample log file (`logs/sample.log`) is included so the dashboard has data on first run.

---

## Configuration

All settings live in `config.yml`:

```yaml
ingestion:
  watch_paths:
    - "logs/"           # folders to monitor (add more paths as needed)
  extensions:
    - ".log"
    - ".txt"

web:
  host: "127.0.0.1"
  port: 5000
  refresh_interval: 15  # dashboard auto-refresh in seconds
```

To monitor a different folder (e.g. your system's actual log directory), add it to `watch_paths`:

```yaml
# Windows example
watch_paths:
  - "logs/"
  - "C:/Windows/System32/winevt/"

# Linux example
watch_paths:
  - "logs/"
  - "/var/log/"
```

---

## Adding Custom Detection Rules

Rules are defined in `rules/default_rules.json`. Each rule looks like this:

```json
{
  "id": "rule_009",
  "name": "My Custom Rule",
  "description": "Detects something suspicious",
  "enabled": true,
  "type": "regex",
  "pattern": "suspicious_keyword|another_pattern",
  "severity": "high",
  "source_filter": null
}
```

| Field | Options | Description |
|---|---|---|
| `type` | `keyword` or `regex` | `keyword` = simple text match; `regex` = regular expression |
| `severity` | `critical` `high` `medium` `low` `info` | How serious the match is |
| `source_filter` | any string or `null` | Only apply rule to files whose name contains this string |
| `enabled` | `true` or `false` | Disable a rule without deleting it |

Restart the server after editing rules.

---

## REST API

| Endpoint | Description |
|---|---|
| `GET /api/stats` | Dashboard summary (counts, timeline, top sources) |
| `GET /api/events` | Paginated event list (`?limit=50&offset=0&severity=high`) |
| `GET /api/alerts` | Paginated alert list (`?limit=50&offset=0`) |

---

## Project Structure

```
SIEM_Platform_Design_v1/
├── main.py                  # Entry point
├── config.yml               # Configuration
├── requirements.txt
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── database.py          # SQLite helpers
│   ├── routes.py            # Web routes + API
│   ├── static/css/          # Stylesheet
│   └── templates/           # HTML pages
├── engine/
│   └── rules_engine.py      # Rule evaluation logic
├── ingestion/
│   └── file_watcher.py      # Real-time log tailing
├── rules/
│   └── default_rules.json   # Detection rules
└── logs/
    └── sample.log           # Demo log data
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite (built into Python) |
| Log monitoring | Watchdog |
| Frontend | Bootstrap 5, Chart.js |
| Config | YAML |

---

## License

MIT — free to use, modify, and distribute.
