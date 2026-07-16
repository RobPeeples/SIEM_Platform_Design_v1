import sqlite3
import os
from datetime import datetime


_DB_PATH = None


def init_db(db_path: str):
    global _DB_PATH
    _DB_PATH = db_path
    conn = _connect()
    _create_tables(conn)
    conn.close()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT    NOT NULL,
            source    TEXT    NOT NULL,
            severity  TEXT    NOT NULL DEFAULT 'info',
            message   TEXT    NOT NULL,
            raw_log   TEXT
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  TEXT    NOT NULL,
            rule_id    TEXT    NOT NULL,
            rule_name  TEXT    NOT NULL,
            severity   TEXT    NOT NULL,
            message    TEXT    NOT NULL,
            event_id   INTEGER REFERENCES events(id)
        );

        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
    """)
    conn.commit()


def insert_event(source: str, severity: str, message: str, raw_log: str = None) -> int:
    conn = _connect()
    ts = datetime.utcnow().isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO events (timestamp, source, severity, message, raw_log) VALUES (?,?,?,?,?)",
        (ts, source, severity, message, raw_log),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def insert_alert(rule_id: str, rule_name: str, severity: str, message: str, event_id: int):
    conn = _connect()
    ts = datetime.utcnow().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO alerts (timestamp, rule_id, rule_name, severity, message, event_id) "
        "VALUES (?,?,?,?,?,?)",
        (ts, rule_id, rule_name, severity, message, event_id),
    )
    conn.commit()
    conn.close()


def get_events(limit: int = 200, offset: int = 0, severity: str = None, source: str = None):
    conn = _connect()
    query = "SELECT * FROM events"
    params = []
    filters = []
    if severity:
        filters.append("severity = ?")
        params.append(severity)
    if source:
        filters.append("source LIKE ?")
        params.append(f"%{source}%")
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_alerts(limit: int = 200, offset: int = 0):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = _connect()
    total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    total_alerts = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]

    severity_counts = {
        row["severity"]: row["cnt"]
        for row in conn.execute(
            "SELECT severity, COUNT(*) as cnt FROM events GROUP BY severity"
        ).fetchall()
    }

    # Events per hour for the last 24 hours
    timeline = conn.execute("""
        SELECT strftime('%Y-%m-%dT%H:00:00', timestamp) as hour, COUNT(*) as cnt
        FROM events
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY hour
        ORDER BY hour
    """).fetchall()

    top_sources = conn.execute("""
        SELECT source, COUNT(*) as cnt
        FROM events
        GROUP BY source
        ORDER BY cnt DESC
        LIMIT 10
    """).fetchall()

    recent_alerts = conn.execute(
        "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 5"
    ).fetchall()

    conn.close()
    return {
        "total_events": total_events,
        "total_alerts": total_alerts,
        "severity_counts": severity_counts,
        "timeline": [dict(r) for r in timeline],
        "top_sources": [dict(r) for r in top_sources],
        "recent_alerts": [dict(r) for r in recent_alerts],
    }
