from datetime import datetime
from pprint import pprint as pp

from pyaviso import NotificationManager, user_config


# Constants
LISTENER_EVENT = "data"  # Event for the listener, options are mars and dissemination
TRIGGER_TYPE = "echo"  # Type of trigger for the listener
REQUEST = {
    "class": "rd",
    "expver": "i7yv",
    "stream": "oper",
    "step": [1, 2, 3],
    "levtype": "sfc",
    "type": "fc",
}  # Request configuration for the listener
CONFIG = {
    "notification_engine": {
        "host": "aviso.apps.lumi.ewctest.link",
        "port": 443,
        "https": True,
    },
    "configuration_engine": {
        "host": "aviso.apps.lumi.ewctest.link",
        "port": 443,
        "https": True,
    },
    "schema_parser": "generic",
    "remote_schema": True,
    "auth_type": "none",
}  # manually defined configuration


def create_listener():
    """
    Creates and returns a listener configuration.
    """

    trigger = {"type": TRIGGER_TYPE}  # Define the trigger for the listener
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
        nm.listen(listeners=listeners_config, config=config)  # Start listening
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")


if __name__ == "__main__":
    main()
