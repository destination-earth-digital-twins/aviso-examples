"""
Register multiple listeners with different filters in a single Aviso session.

This example shows two parallel subscriptions:
1. Surface forecast products (oper stream) → Python function callback.
2. Wave forecast products (wave stream) → Echo to stdout.

Both listeners run concurrently. This is the recommended pattern for reacting
differently to different types of Extremes-DT products.
"""

from datetime import datetime
from pprint import pprint as pp

from pyaviso import NotificationManager, user_config

# ============================================================================
# CONFIGURATION
# ============================================================================

# Listener event type (must be "data" for Extremes-DT)
LISTENER_EVENT = "data"

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


def on_surface(notification):
    """Process surface forecast notifications."""
    req = notification.get("request", {})
    print(
        "[surface] base={date} {time}Z step={step} ready".format(
            date=req.get("date"),
            time=req.get("time"),
            step=req.get("step"),
        )
    )


# ============================================================================
# LISTENER SETUP
# ============================================================================


def create_surface_listener():
    """Construct surface forecast listener."""
    return {
        "event": LISTENER_EVENT,
        "request": {
            "class": "d1",
            "expver": "0001",
            "stream": "oper",
            "type": "fc",
            "levtype": "sfc",
            "step": [0, 3, 6, 9, 12, 15, 18, 21, 24],
        },
        "triggers": [{"type": "function", "function": on_surface}],
    }


def create_wave_listener():
    """Construct wave forecast listener."""
    return {
        "event": LISTENER_EVENT,
        "request": {
            "class": "d1",
            "expver": "0001",
            "stream": "wave",
            "type": "fc",
        },
        "triggers": [{"type": "echo"}],
    }


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Start listening for both surface and wave notifications."""
    try:
        surface_listener = create_surface_listener()
        wave_listener = create_wave_listener()
        listeners_config = {
            "listeners": [surface_listener, wave_listener],
        }
        config = user_config.UserConfig(**CONFIG)
        print("Loaded Aviso configuration:")
        pp(CONFIG)
        nm = NotificationManager()
        print(f"Listening for {LISTENER_EVENT} notifications on /de/data/ ...")
        print("Stop with Ctrl+C.\n")
        nm.listen(listeners=listeners_config, config=config, from_date=START_DATE)
    except KeyboardInterrupt:
        print("\nListener stopped.")
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")


if __name__ == "__main__":
    main()
