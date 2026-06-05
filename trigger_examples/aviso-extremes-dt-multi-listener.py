"""
Register multiple listeners with different request filters in a single
Aviso session.

This example shows two parallel subscriptions, each with its own filter and
action, both connected to the same Aviso endpoint:

    1. Surface forecast steps (every 3h up to 24h) -> Python function.
    2. Wave-stream forecast products              -> echo to stdout.

A single `NotificationManager.listen(...)` call handles both. This is the
recommended pattern when you need to react differently to different kinds of
Extremes-DT products from the same process.

"""

from pprint import pprint as pp

from pyaviso import NotificationManager, user_config

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


def on_surface(notification):
    req = notification.get("request", {})
    print(
        "[surface] base={date} {time}Z step={step} "
        "ready".format(
            date=req.get("date"),
            time=req.get("time"),
            step=req.get("step"),
        )
    )


def main():
    surface_listener = {
        "event": "data",
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

    wave_listener = {
        "event": "data",
        "request": {
            "class": "d1",
            "expver": "0001",
            "stream": "wave",
            "type": "fc",
        },
        "triggers": [{"type": "echo"}],
    }

    config = user_config.UserConfig(**CONFIG)
    nm = NotificationManager()
    print("loaded config:")
    pp(CONFIG)
    nm.listen(
        listeners={"listeners": [surface_listener, wave_listener]},
        config=config,
    )


if __name__ == "__main__":
    main()
