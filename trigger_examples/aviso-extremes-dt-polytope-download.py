"""
On every Extremes-DT data-availability notification, download the corresponding
GRIB field from Polytope and save it to a local directory. No plotting, no
regridding -- this is the minimal "notification -> bytes on disk" pipeline.

Requires:
  * A valid DESP token, obtained via `python desp-authentication.py`
    (written by default to `~/.polytopeapirc`).
  * `earthkit-data` and `polytope-client` installed.

"""

from datetime import datetime
from pathlib import Path
from pprint import pprint as pp

import earthkit.data
from pyaviso import NotificationManager, user_config

# Where to write GRIB files. Created on demand.
OUT_DIR = Path("downloads/extremes-dt")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Replay/start position. Publication time, NOT forecast base time.
START_DATE = datetime(2025, 11, 4)

# 2 metre temperature (param=167) on the surface forecast stream.
REQUEST = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    "step": [0, 6, 12, 18, 24],
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
    polytope_request = {
        "class": "d1",
        "expver": "0001",
        "stream": "oper",
        "type": "fc",
        "levtype": "sfc",
        "date": req["date"],
        "time": req["time"],
        "step": req["step"],
        "param": "167",  # 2m temperature
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
    data.to_target("file")
    print(f"done: {out_path} ({out_path.stat().st_size / 1024:.1f} KiB)")


def main():
    listener = {
        "event": "data",
        "request": REQUEST,
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
