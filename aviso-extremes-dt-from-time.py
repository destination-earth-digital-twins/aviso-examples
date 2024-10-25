from datetime import datetime
from pprint import pprint as pp

from pyaviso import NotificationManager, user_config

# Constants
START_DATE = datetime(1999, 12, 12)  # Start date for the notification listener
LISTENER_EVENT = "data"  # Event for the listener, options are mars and dissemination
TRIGGER_TYPE = "function"  # Type of trigger for the listener
REQUEST = {
    "class": "d1",
    "expver": "0001",
    "stream": "wave",
    "step": [1, 2, 3],
    "levtype": "sfc",
    "type": "fc",
}  # Request configuration for the listener
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
}  # manually defined configuration


def do_something(notification):
    """
    Function for the listener to trigger.
    """
    pp(notification)


def create_listener():
    """
    Creates and returns a listener configuration.
    """

    trigger = {
        "type": TRIGGER_TYPE,
        "function": do_something,
    }  # Define the trigger for the listener
    # Return the complete listener configuration
    return {"event": LISTENER_EVENT, "request": REQUEST, "triggers": [trigger]}


def main():
    try:
        listener = create_listener()  # Create listener configuration
        listeners_config = {"listeners": [listener]}  # Define listeners configuration
        config = user_config.UserConfig(**CONFIG)
        print("loaded config:")
        pp(CONFIG)
        nm = NotificationManager()  # Initialize the NotificationManager

        nm.listen(
            listeners=listeners_config, from_date=START_DATE, config=config
        )  # Start listening
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")


if __name__ == "__main__":
    main()
