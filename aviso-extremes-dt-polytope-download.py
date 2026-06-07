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
from pathlib import Path
from pprint import pprint as pp
from datetime import datetime, timedelta

import earthkit.data
from pyaviso import NotificationManager, user_config


# Where to write GRIB files. Created on demand.
OUT_DIR = Path("downloads/")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Replay/start position. Publication time, NOT forecast base time.
START_DATE = datetime.now() - timedelta(days=2)

AVISO_REQUEST = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    "step": [0, 6, 12],
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


def download(notification):
    req = notification.get("request", {})

    LOCATION = ((38, -9.5))

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
        "param": "167",  # Download only 2m temperature
        "feature": {
            "type" : "timeseries",
            "points": [[LOCATION[0], LOCATION[1]]],
            "time_axis": "date",
        }
    }

    out_path = OUT_DIR / (
        f"t2m_{req['date']}_{req['time']}_step{req['step']}.grib"
    )
    if out_path.exists():
        print(f"skip (exists): {out_path.name}")
        return

    print(f"downloading -> {out_path}")
    pp(polytope_request)

    data = earthkit.data.from_source(
        "polytope",
        "destination-earth",
        polytope_request,
        address="polytope.lumi.apps.dte.destination-earth.eu",
        stream=False,
    )
    data.to_target("file", out_path)
    print(f"done: {out_path} ({out_path.stat().st_size / 1024:.1f} KiB)")


def main():
    listener = {
        "event": "data",
        "request": AVISO_REQUEST,
        "triggers": [{"type": "function", "function": download}],
    }
    config = user_config.UserConfig(**CONFIG)
    nm = NotificationManager()
    print(f"Writing GRIB downloads to {OUT_DIR.resolve()}")
    nm.listen(
        listeners={"listeners": [listener]},
        from_date=START_DATE,
        config=config,
    )


if __name__ == "__main__":
    main()
