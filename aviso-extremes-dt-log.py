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

# ============================================================================
# CONFIGURATION
# ============================================================================

# Output file with timestamp to avoid overwrites
SCRIPT_NAME = Path(__file__).stem
RUN_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
LOG_PATH = Path(f"{SCRIPT_NAME}_{RUN_TIMESTAMP}.jsonl")

# Listener event type (must be "data" for Extremes-DT)
LISTENER_EVENT = "data"

# Trigger type: "echo" prints to stdout, "function" calls a Python function
TRIGGER_TYPE = "function"

# Request filter: narrow to surface forecast products of Extremes DT
AVISO_REQUEST = {
    "class": "d1",
    "date": "20260602",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    "step": [0, 3, 6, 9, 12, 15, 18, 21, 24],
}

# Aviso server and notification engine configuration
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

# ============================================================================
# TRIGGER FUNCTIONS
# ============================================================================


def append_to_log(notification):
    """Append notification with timestamp to a JSON-lines log file."""
    record = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "notification": notification,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")
    pp(record)


# ============================================================================
# LISTENER SETUP
# ============================================================================


def create_listener():
    """Construct a listener configuration for Extremes-DT notifications."""
    trigger = {
        "type": TRIGGER_TYPE,
        "function": append_to_log,
    }
    return {
        "event": LISTENER_EVENT,
        "request": AVISO_REQUEST,
        "triggers": [trigger],
    }


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Listen for notifications and append each to a JSON-lines log file."""
    try:
        listener = create_listener()
        listeners_config = {"listeners": [listener]}
        config = user_config.UserConfig(**CONFIG)
        print(f"Logging Extremes-DT notifications to {LOG_PATH.resolve()}")
        print(f"Stop with Ctrl+C.\n")
        nm = NotificationManager()
        nm.listen(listeners=listeners_config, config=config)
    except KeyboardInterrupt:
        print(f"\nLogging stopped. Output saved to {LOG_PATH.resolve()}")
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")


if __name__ == "__main__":
    main()
