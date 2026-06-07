"""
Replay notifications from a past publish time, then continue listening live.

Unlike the real-time listener, this script:
- Replays notifications from START_DATE onward.
- Catches up any missed notifications.
- Then continues listening to new notifications.

This is useful for recovery after outages or to backfill initial setup.
"""

from datetime import datetime
from pprint import pprint as pp

from pyaviso import NotificationManager, user_config

# ============================================================================
# CONFIGURATION
# ============================================================================

# Replay start point: publication time, not forecast base time
START_DATE = datetime(2025, 11, 4)

# Listener event type (must be "data" for Extremes-DT)
LISTENER_EVENT = "data"

# Trigger type: "echo" prints to stdout, "function" calls a Python function
TRIGGER_TYPE = "function"

# Request filter: only notifications matching ALL keys are delivered
AVISO_REQUEST = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "step": [0, 3, 6, 9, 12, 15, 18, 21, 24],
    "levtype": "sfc",
    "type": "fc",
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


def do_something(notification):
    """Print the received notification."""
    pp(notification)


# ============================================================================
# LISTENER SETUP
# ============================================================================


def create_listener():
    """Construct a listener configuration for Extremes-DT notifications."""
    trigger = {
        "type": TRIGGER_TYPE,
        "function": do_something,
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
    """Replay from START_DATE, then continue listening for new notifications."""
    try:
        listener = create_listener()
        listeners_config = {"listeners": [listener]}
        config = user_config.UserConfig(**CONFIG)
        print("Loaded Aviso configuration:")
        pp(CONFIG)
        nm = NotificationManager()
        print(f"Replaying notifications from {START_DATE.isoformat()} UTC ...")
        print("Stop with Ctrl+C.\n")
        nm.listen(listeners=listeners_config, from_date=START_DATE, config=config)
    except KeyboardInterrupt:
        print("\nListener stopped.")
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")


if __name__ == "__main__":
    main()
