"""
Structured event logging for GYRO Honeypot.
Every connection attempt is written as one JSON line to logs/events.jsonl
so logs stay greppable, diffable, and easy to pipe into other tools later.
"""

import json
import os
import datetime
import asyncio


class EventLogger:
    def __init__(self, log_dir: str = "logs", log_file: str = "events.jsonl"):
        self.log_dir = log_dir
        self.log_path = os.path.join(log_dir, log_file)
        os.makedirs(self.log_dir, exist_ok=True)
        self._lock = asyncio.Lock()

    async def log_event(self, event: dict) -> None:
        """Append one event as a JSON line. Thread/async-safe via lock."""
        event.setdefault("timestamp", datetime.datetime.utcnow().isoformat() + "Z")
        line = json.dumps(event, ensure_ascii=False)
        async with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def read_recent(self, limit: int = 20) -> list:
        """Read the last `limit` events for the dashboard. Sync, small file reads are cheap."""
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        events = []
        for line in lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events
