"""
Entry point for the Home Lab SIEM.

Usage:
  python main.py          # starts with settings from config.yml
  python main.py --dev    # forces debug/reload mode (recommended during development)
"""
import sys
import threading

import yaml

from app import create_app, load_config
from engine.rules_engine import load_rules
from ingestion.file_watcher import start_watcher


def main():
    dev_mode = "--dev" in sys.argv

    config = load_config()
    siem_cfg = config["siem"]
    web_cfg = config["web"]
    ingest_cfg = config["ingestion"]
    rules_path = config["rules"]["path"]

    # create_app() must run first — it calls init_db()
    app = create_app()

    # Load alert rules
    load_rules(rules_path)
    print(f"[siem] Rules loaded from {rules_path}")

    # Ingest any existing content in watched log files on startup
    _ingest_existing(ingest_cfg)

    # Start file watcher in background thread
    observer = start_watcher(
        watch_paths=ingest_cfg["watch_paths"],
        extensions=ingest_cfg["extensions"],
    )
    print(f"[siem] Watching: {ingest_cfg['watch_paths']}")

    host = web_cfg["host"]
    port = web_cfg["port"]
    debug = dev_mode or web_cfg.get("debug", False)

    print(f"[siem] Starting web UI at http://{host}:{port}")
    if debug:
        print("[siem] Running in DEV mode — Flask will auto-reload on code changes")

    try:
        # use_reloader=False so we manage threads ourselves; debug still works
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    finally:
        observer.stop()
        observer.join()


def _ingest_existing(ingest_cfg: dict):
    """Read log files that already exist in watched paths on startup."""
    import os
    from app.database import insert_event
    from engine.rules_engine import evaluate

    extensions = [e.lower() for e in ingest_cfg["extensions"]]
    for watch_path in ingest_cfg["watch_paths"]:
        abs_path = os.path.abspath(watch_path)
        if not os.path.isdir(abs_path):
            continue
        for fname in os.listdir(abs_path):
            if any(fname.lower().endswith(ext) for ext in extensions):
                fpath = os.path.join(abs_path, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            line = line.rstrip("\n\r")
                            if line.strip():
                                sev = _infer_severity(line)
                                eid = insert_event(
                                    source=fname,
                                    severity=sev,
                                    message=line[:500],
                                    raw_log=line,
                                )
                                evaluate(line, fname, sev, eid)
                    print(f"[siem] Ingested: {fname}")
                except OSError as e:
                    print(f"[siem] Could not read {fname}: {e}")


def _infer_severity(line: str) -> str:
    lower = line.lower()
    if any(w in lower for w in ("critical", "emerg", "fatal")):
        return "critical"
    if any(w in lower for w in ("error", "err", "fail", "denied")):
        return "high"
    if any(w in lower for w in ("warn", "warning")):
        return "medium"
    if any(w in lower for w in ("notice", "info")):
        return "info"
    return "low"


if __name__ == "__main__":
    main()
