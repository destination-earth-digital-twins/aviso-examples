"""
Persist every Extremes-DT data-availability notification to a JSON-lines log
file using a Python `function` trigger.

This is a more durable alternative to the `echo` trigger: each notification is
appended as one JSON document per line to `aviso-extremes-dt-log-<timestamp>.jsonl`.

"""

import json
from datetime import datetime, timezone
from pathlib import Path
from pprint import pprint as pp

from pyaviso import NotificationManager, user_config

SCRIPT_NAME = Path(__file__).stem
RUN_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
LOG_PATH = Path(f"{SCRIPT_NAME}_{RUN_TIMESTAMP}.jsonl")

# Narrow the subscription to surface forecast products of the Extremes DT
# for basetime 2026-06-02 and for specific steps. Adjust as needed.
AVISO_REQUEST = {
    "class": "d1",
    "date": "20260602",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    "step": [0, 3, 6, 9, 12, 15, 18, 21, 24],
}

CONFIG = {
    "notification_engine": {
        "host": "aviso.lumi.apps.dte.destination-earth.eu",
        "port": 443,
        "https": True,
    },
    "configuration_engine": {
        "host": "aviso.lumi.apps.dte.destination-earth.eu",
        "port": 443,
        "https": True,
    },
    "schema_parser": "generic",
    "remote_schema": True,
    "auth_type": "none",
}


def append_to_log(notification):
    """Trigger function: enrich and append the notification to a JSONL file."""
    record = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "notification": notification,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")
    pp(record)


def main():
    listener = {
        "event": "data",
        "request": AVISO_REQUEST,
        "triggers": [{"type": "function", "function": append_to_log}],
    }
    config = user_config.UserConfig(**CONFIG)
    nm = NotificationManager()
    print(f"Logging Extremes-DT notifications to {LOG_PATH.resolve()}")
    nm.listen(
        listeners={"listeners": [listener]},
        from_date=datetime(2026, 6, 2),
        to_date=datetime(2026, 6, 3), # listen for 1 day after basetime in case forecast products arrive with delay
        config=config)


if __name__ == "__main__":
    main()
