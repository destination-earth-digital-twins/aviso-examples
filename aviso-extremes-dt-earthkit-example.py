from datetime import datetime
from pprint import pprint as pp

import earthkit.data
import earthkit.plots
import earthkit.regrid
from pyaviso import NotificationManager, user_config

# Constants
START_DATE = datetime(2025, 11, 5)  # Start date for the notification listener
LISTENER_EVENT = "data"  # Event for the listener, options are mars and dissemination
TRIGGER_TYPE = "function"  # Type of trigger for the listener
REQUEST = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "step": [0, 3, 6, 9, 12, 15, 18, 21, 24],
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

    #    for key, value in notification.items():
    #        print(key, value)

    notification_dic = notification["request"]
    rdate = notification_dic["date"]
    rtime = notification_dic["time"]
    rstep = notification_dic["step"]

    # This request matches a single parameter of the extremes DT, at 4km resolution
    # which began production on 2023-12-11

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

    data.ls()

    data.to_xarray(engine="cfgrib")

    # regrid to 1x1 degree
    out_grid = {"grid": [0.1, 0.1]}
    data_interpolated = earthkit.regrid.interpolate(
        data, out_grid=out_grid, method="linear"
    )
    data_interpolated.to_xarray(engine="cfgrib")

    chart = earthkit.plots.Map(domain="Europe")
    chart.quickplot(data_interpolated[0])

    chart.title("Temperature at 2m")
    chart.coastlines()
    chart.gridlines()
    chart.show()


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
