"""
Minimal real-time listener for Extremes-DT data-availability notifications.

This script demonstrates the simplest listening pattern:
- Define a request filter for Extremes-DT products.
- Use the `echo` trigger to print notifications to stdout.
- Continue listening until interrupted (Ctrl+C).
"""

from pprint import pprint as pp

from pyaviso import NotificationManager, user_config

# ============================================================================
# CONFIGURATION
# ============================================================================

# Listener event type (must be "data" for Extremes-DT)
LISTENER_EVENT = "data"

# Trigger type: "echo" prints to stdout, "function" calls a Python function
TRIGGER_TYPE = "echo"

# Request filter: only notifications matching ALL keys are delivered
AVISO_REQUEST = {
    "class": "d1",
    "expver": "0001",
    "stream": "wave",
    "step": [1, 2, 3],
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
# LISTENER SETUP
# ============================================================================


def create_listener():
    """Construct a listener configuration for Extremes-DT notifications."""
    trigger = {"type": TRIGGER_TYPE}
    return {
        "event": LISTENER_EVENT,
        "request": AVISO_REQUEST,
        "triggers": [trigger],
    }


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Start listening for real-time Extremes-DT data notifications."""
    try:
        listener = create_listener()
        listeners_config = {"listeners": [listener]}
        config = user_config.UserConfig(**CONFIG)
        print("Loaded Aviso configuration:")
        pp(CONFIG)
        nm = NotificationManager()
        print(f"Listening for {LISTENER_EVENT} notifications on /de/data/ ...")
        print("Stop with Ctrl+C.\n")
        nm.listen(listeners=listeners_config, config=config)
    except KeyboardInterrupt:
        print("\nListener stopped.")
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")


if __name__ == "__main__":
    main()
