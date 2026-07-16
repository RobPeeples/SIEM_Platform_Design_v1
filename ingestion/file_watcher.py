"""
Watches directories for new/modified log files and tails new lines into the database.
"""
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.database import insert_event
from engine.rules_engine import evaluate


class _LogFileHandler(FileSystemEventHandler):
    def __init__(self, extensions: list[str]):
        self._extensions = [e.lower() for e in extensions]
        # Track read position per file
        self._positions: dict[str, int] = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if any(path.lower().endswith(ext) for ext in self._extensions):
            self._tail(path)

    def on_created(self, event):
        if not event.is_directory:
            self.on_modified(event)

    def _tail(self, path: str):
        try:
            pos = self._positions.get(path, 0)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(pos)
                for line in f:
                    line = line.rstrip("\n\r")
                    if line.strip():
                        self._process_line(line, source=os.path.basename(path))
                self._positions[path] = f.tell()
        except OSError:
            pass

    def _process_line(self, line: str, source: str):
        severity = _infer_severity(line)
        event_id = insert_event(
            source=source,
            severity=severity,
            message=line[:500],  # cap stored message length
            raw_log=line,
        )
        evaluate(line, source, severity, event_id)


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


def start_watcher(watch_paths: list[str], extensions: list[str]) -> Observer:
    handler = _LogFileHandler(extensions)
    observer = Observer()
    for path in watch_paths:
        abs_path = os.path.abspath(path)
        os.makedirs(abs_path, exist_ok=True)
        observer.schedule(handler, abs_path, recursive=True)
    observer.start()
    return observer
