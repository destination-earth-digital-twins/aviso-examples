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

Run with:
    python examples/aviso-extremes-dt-replay-window.py
"""

from datetime import datetime
from pprint import pprint as pp

from pyaviso import NotificationManager, user_config

# Publication-time window (UTC). Choose a window strictly in the past.
FROM_DATE = datetime(2025, 11, 3)
TO_DATE = datetime(2025, 11, 5)

REQUEST = {
    "class": "d1",
    "dataset": "extremes-dt",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    # Optionally narrow to a specific forecast cycle:
    # "date": "20251104",
    # "time": "0000",
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


def count_and_print(notification, _counter=[0]):
    _counter[0] += 1
    req = notification.get("request", {})
    print(
        f"[{_counter[0]:04d}] base={req.get('date')} {req.get('time')}Z "
        f"step={req.get('step')} stream={req.get('stream')}"
    )


def main():
    listener = {
        "event": "data",
        "request": REQUEST,
        "triggers": [{"type": "function", "function": count_and_print}],
    }
    config = user_config.UserConfig(**CONFIG)
    nm = NotificationManager()
    print("Replaying notifications published between "
          f"{FROM_DATE.isoformat()} and {TO_DATE.isoformat()} UTC")
    print("filter:")
    pp(REQUEST)
    nm.listen(
        listeners={"listeners": [listener]},
        from_date=FROM_DATE,
        to_date=TO_DATE,
        config=config,
    )
    print("Replay complete.")


if __name__ == "__main__":
    main()
