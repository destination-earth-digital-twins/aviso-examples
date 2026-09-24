"""
On every Extremes-DT data-availability notification, download the corresponding
data from Polytope and save it to a local directory. No plotting, no
regridding -- this is the minimal "notification -> bytes on disk" pipeline.

A polytope feature extraction is used to download only the 2m temperature
time series at a single location, to learn more about polytope feature extraction
visit https://github.com/destination-earth-digital-twins/polytope-examples

A feature extraction returns CoverageJSON rather than GRIB, so each result is
saved as a `.covjson` file.

Requires:
  * A valid DESP token, obtained via `python desp-authentication.py` in the
    repository root. It writes both the Polytope token (`~/.polytopeapirc`)
    and the Aviso credential (`~/.config/aviso/credentials.yaml`).
  * `earthkit-data` and `polytope-client` installed.
"""

import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import earthkit.data
import pyaviso

# ============================================================================
# CONFIGURATION
# ============================================================================

# Aviso server for pyaviso 2. The credential is found automatically in
# ~/.config/aviso/credentials.yaml.
AVISO_URL = "https://aviso2.lumi.apps.dte.destination-earth.eu"

# Output directory for downloaded files
OUT_DIR = Path(__file__).parent / "downloads"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Replay/start position: publication time (UTC), NOT forecast base time
START_DATE = datetime.now(timezone.utc) - timedelta(days=13)

# Event type (always "data" for Extremes-DT)
EVENT_TYPE = "data"

# Filter: only notifications matching ALL keys are delivered
FILTER = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    "step": {"in": [0, 6, 12]},
}

# ============================================================================
# PROCESSING
# ============================================================================


def download(notification):
    """Download and save the 2m temperature time series for the notified step."""
    req = notification.identifier

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

    out_file = f"t2m_{req['date']}_{req['time']}_step{req['step']}.covjson"
    out_path = OUT_DIR / out_file

    print(f"Downloading -> {out_file}")

    data = earthkit.data.from_source(
        "polytope",
        "destination-earth",
        polytope_request,
        address="polytope.lumi.apps.dte.destination-earth.eu",
        stream=False,
    )

    # earthkit-data keeps the downloaded CoverageJSON at data.path
    shutil.copyfile(data.path, out_path)
    print(f"Done: {out_path} ({out_path.stat().st_size / 1024:.1f} KiB)")


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Start listening and download data for each notification."""
    start = START_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        client = pyaviso.AvisoClient(base_url=AVISO_URL)
        print(client.config)
        print("Downloading Extremes-DT notifications")
        print(f"Replaying from {start}")
        print("Stop with Ctrl+C.\n")
        with client.listen(
            EVENT_TYPE, filter=FILTER, start_from=start
        ) as notifications:
            for notification in notifications:
                try:
                    download(notification)
                except Exception as e:
                    # One failed download must not stop the listener.
                    print(f"Skipped #{notification.sequence}: {e}")
    except KeyboardInterrupt:
        print(f"\nListener stopped. Downloads saved in {OUT_DIR}")
    except pyaviso.HistoryGapError as e:
        if e.reason == "replay_limit_reached":
            sys.exit(
                "Replay stopped: more notifications match than the server "
                "replays at once. Narrow FILTER or start later."
            )
        sys.exit(f"Aviso error: {e}")
    except pyaviso.AvisoError as e:
        sys.exit(f"Aviso error: {e}")


if __name__ == "__main__":
    main()
