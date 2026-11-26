"""Sends a TEST alert email using the 3 most recent high-risk or Jamaica-linked incidents already on the site.
Nothing is marked as alerted, so real alerts are not affected."""
import json
import os
import sys

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from watch import alerts  # noqa: E402

with open(os.path.join(HERE, "config.yaml"), encoding="utf-8") as f:
    site = yaml.safe_load(f).get("site") or {}
with open(os.path.join(HERE, "data", "events.json"), encoding="utf-8") as f:
    events = json.load(f)
pick = [dict(e, first_seen="TEST", alerted=False) for e in sorted(events, key=lambda e: e.get("date", ""), reverse=True)
        if e.get("kind") == "Incident" and (e.get("level") == "High" or e.get("home"))][:3]
n = alerts.send(pick, "TEST", dict(site, title="TEST"), subject_prefix="[TEST] ")
sys.exit(0 if n else 1)
