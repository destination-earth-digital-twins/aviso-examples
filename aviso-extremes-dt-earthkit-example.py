"""
End-to-end Extremes-DT processing workflow: notification → data download → regrid → plot.

When a new Extremes-DT forecast becomes available, this script:
1. Receives the data-availability notification.
2. Downloads the corresponding field via Polytope.
3. Regrids to coarser resolution for faster processing.
4. Generates a map plot focused on Europe.

Requires earthkit-data, earthkit-plots, earthkit-regrid and polytope-client.
"""

from datetime import datetime, timedelta
from pprint import pprint as pp

import matplotlib
matplotlib.use('agg')

import earthkit.data
import earthkit.plots
import earthkit.regrid
from pyaviso import NotificationManager, user_config

# ============================================================================
# CONFIGURATION
# ============================================================================

# Replay start point: publication time, not forecast base time
FROM_DATE = datetime.now() - timedelta(days=14)

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
    """Download, regrid, and plot temperature data on notification."""
    pp(notification)

    #    for key, value in notification.items():
    #        print(key, value)

    notification_dic = notification["request"]
    rdate = notification_dic["date"]
    rtime = notification_dic["time"]
    rstep = notification_dic["step"]

    # Download 2m temperature (param=167) from Extremes DT at 4 km resolution

    request = {
        "class": "d1",
        "expver": "0001",
        "stream": "oper",
        "dataset": "extremes-dt",
        "date": rdate,
        "time": rtime,
        "type": "fc",
        "levtype": "sfc",
        "step": rstep,
        "param": "167",
    }

    # data is an earthkit streaming object but with stream=False will download data immediately
    data = earthkit.data.from_source(
        "polytope",
        "destination-earth",
        request,
        address="polytope.lumi.apps.dte.destination-earth.eu",
        stream=False,
    )

    data.to_xarray()

    # regrid to 1x1 degree
    out_grid = {"grid": [0.1, 0.1]}
    data_interpolated = earthkit.regrid.interpolate(
        data, out_grid=out_grid, method="linear"
    )
    data_interpolated.to_xarray()

    chart = earthkit.plots.Map(domain="Europe")
    chart.quickplot(data_interpolated[0])

    chart.title("{variable_name} in {time}")
    chart.coastlines()
    chart.gridlines()
    chart.save(f"2t-extremes-dt-{rdate}{rtime}Z-step{rstep}.png")
    chart.show()


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
    """Start listening for Extremes-DT notifications and process each one."""
    try:
        listener = create_listener()
        listeners_config = {"listeners": [listener]}
        config = user_config.UserConfig(**CONFIG)
        print("Loaded Aviso configuration:")
        pp(CONFIG)
        nm = NotificationManager()
        print(f"Replaying notifications from {FROM_DATE.isoformat()} UTC ...")
        print("Stop with Ctrl+C.\n")
        nm.listen(listeners=listeners_config, from_date=FROM_DATE, config=config)
    except KeyboardInterrupt:
        print("\nListener stopped.")
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")


if __name__ == "__main__":
    main()
