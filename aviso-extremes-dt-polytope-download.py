"""
On every Extremes-DT data-availability notification, download the corresponding
GRIB field from Polytope and save it to a local directory. No plotting, no
regridding -- this is the minimal "notification -> bytes on disk" pipeline.

A polytope feature extraction is used to download only the 2m temperature
time series at a single location, to learn more about polytope feature extraction
visit https://github.com/destination-earth-digital-twins/polytope-examples

Requires:
  * A valid DESP token, obtained via `python desp-authentication.py`
    (written by default to `~/.polytopeapirc`).
  * `earthkit-data` and `polytope-client` installed.

"""
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pprint as pp

import earthkit.data
from pyaviso import NotificationManager, user_config

# ============================================================================
# CONFIGURATION
# ============================================================================

# Replay/start position: publication time, NOT forecast base time
START_DATE = datetime.now() - timedelta(days=13)

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
    "step": [0, 6, 12],
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


def download(notification):
    """Download and save GRIB data for the notified forecast step."""
    req = notification.get("request", {})

    # Example location: Lisbon, Portugal
    LOCATION = (38, -9.5)

    polytope_request = {
        "dataset": "extremes-dt",
        "class": "d1",
        "expver": "0001",
        "stream": "oper",
        "type": "fc",
        "levtype": "sfc",
        "date": req["date"],
        "time": req["time"],
        "step": req["step"],
        "param": "167",  # 2m temperature
        "feature": {
            "type": "timeseries",
            "points": [[LOCATION[0], LOCATION[1]]],
            "time_axis": "date",
        },
    }

    out_file = f"t2m_{req['date']}_{req['time']}_step{req['step']}.grib"
    
    if Path(out_file).exists():
        print(f"skip (exists): {Path(out_file).name}")
        return

    print(f"Downloading -> {out_file}")
    pp(polytope_request)

    data = earthkit.data.from_source(
        "polytope",
        "destination-earth",
        polytope_request,
        address="polytope.lumi.apps.dte.destination-earth.eu",
        stream=False,
    )
    data.to_target("file", out_file)
    print(f"Done: {out_file} ({Path(out_file).stat().st_size / 1024:.1f} KiB)")


# ============================================================================
# LISTENER SETUP
# ============================================================================


def create_listener():
    """Construct a listener configuration for Extremes-DT notifications."""
    trigger = {
        "type": TRIGGER_TYPE,
        "function": download,
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
    """Start listening and download data for each notification."""
    try:
        listener = create_listener()
        listeners_config = {"listeners": [listener]}
        config = user_config.UserConfig(**CONFIG)
        print(f"Downloading Extremes-DT notifications")
        print(f"Replaying from {START_DATE.isoformat()} UTC")
        print(f"Stop with Ctrl+C.\n")
        nm = NotificationManager()
        nm.listen(
            listeners=listeners_config,
            from_date=START_DATE,
            config=config,
        )
    except KeyboardInterrupt:
        print(f"\nListener stopped. Downloads saved")
    except Exception as e:
        print(f"Failed to initialize the Notification Manager: {e}")



if __name__ == "__main__":
    main()
