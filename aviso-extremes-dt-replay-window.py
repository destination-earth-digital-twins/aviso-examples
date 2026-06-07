"""
Replay Extremes-DT notifications inside a bounded historical window and exit.

Unlike `aviso-extremes-dt-from-time.py`, which catches up from a given moment
and then keeps listening, this example uses both `from_date` and `to_date`.
When `to_date` is provided, Aviso terminates after replaying all the
notifications published in that interval.

This is the right pattern when you want to:

  * Rebuild a local index of past notifications,
  * Test a trigger function deterministically against real notifications,
  * Backfill a downstream system without subscribing to the live stream.

IMPORTANT: `from_date`/`to_date` refer to the time the notification was
PUBLISHED on the Aviso server (i.e. when the producer announced the data was
available). They are NOT the forecast base time. To target forecasts
initialised at a specific cycle, use `date`/`time` inside the request and set
the window generously around the production wall-clock.

"""

from datetime import datetime, timedelta
from pprint import pprint as pp

from pyaviso import NotificationManager, user_config

# ============================================================================
# CONFIGURATION
# ============================================================================

# Publication-time window (UTC). Choose a window strictly in the past.
TO_DATE = datetime.now()
FROM_DATE = TO_DATE - timedelta(days=14)

# Listener event type (must be "data" for Extremes-DT)
LISTENER_EVENT = "data"

# Trigger type: "echo" prints to stdout, "function" calls a Python function
TRIGGER_TYPE = "function"

# Request filter: only notifications matching ALL keys are delivered
AVISO_REQUEST = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    # Optionally narrow to a specific forecast cycle:
    # "date": "20251104",
    # "time": "0000",
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


def count_and_print(notification, _counter=[0]):
    """Count and display each notification."""
    _counter[0] += 1
    req = notification.get("request", {})
    print(
        f"[{_counter[0]:04d}] base={req.get('date')} {req.get('time')}Z "
        f"step={req.get('step')} stream={req.get('stream')}"
    )


# ============================================================================
# LISTENER SETUP
# ============================================================================


def create_listener():
    """Construct a listener configuration for Extremes-DT notifications."""
    trigger = {
        "type": TRIGGER_TYPE,
        "function": count_and_print,
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
    """Replay bounded historical window and exit."""
    try:
        listener = create_listener()
        listeners_config = {"listeners": [listener]}
        config = user_config.UserConfig(**CONFIG)
        print("Replaying notifications published between:")
        print(f"  From: {FROM_DATE.isoformat()} UTC")
        print(f"  To:   {TO_DATE.isoformat()} UTC")
        print("Filter:")
        pp(AVISO_REQUEST)
        nm = NotificationManager()
        nm.listen(
            listeners=listeners_config,
            from_date=FROM_DATE,
            to_date=TO_DATE,
            config=config,
        )
        print("\nReplay complete.")
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")


if __name__ == "__main__":
    main()
