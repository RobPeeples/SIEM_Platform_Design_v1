"""
Evaluates log lines against JSON-defined rules and fires alerts.

Rule schema (rules/default_rules.json):
  id          - unique rule identifier
  name        - human-readable name
  description - what the rule detects
  enabled     - true/false
  type        - "keyword" | "regex"
  pattern     - string to match (keyword) or regex pattern (regex)
  severity    - critical | high | medium | low | info
  source_filter - optional substring; only apply rule to matching sources
"""
import json
import re
import os
from typing import Optional


_rules: list[dict] = []
_compiled: dict[str, re.Pattern] = {}


def load_rules(path: str):
    global _rules, _compiled
    with open(path, "r", encoding="utf-8") as f:
        _rules = [r for r in json.load(f) if r.get("enabled", True)]
    _compiled = {}
    for rule in _rules:
        if rule["type"] == "regex":
            try:
                _compiled[rule["id"]] = re.compile(rule["pattern"], re.IGNORECASE)
            except re.error as e:
                print(f"[rules] Bad regex in rule {rule['id']}: {e}")


def evaluate(line: str, source: str, severity: str, event_id: int):
    from app.database import insert_alert

    for rule in _rules:
        src_filter = rule.get("source_filter")
        if src_filter and src_filter.lower() not in source.lower():
            continue

        matched = False
        if rule["type"] == "keyword":
            matched = rule["pattern"].lower() in line.lower()
        elif rule["type"] == "regex":
            pattern = _compiled.get(rule["id"])
            if pattern:
                matched = bool(pattern.search(line))

        if matched:
            insert_alert(
                rule_id=rule["id"],
                rule_name=rule["name"],
                severity=rule["severity"],
                message=f"{rule['name']}: {line[:300]}",
                event_id=event_id,
            )
