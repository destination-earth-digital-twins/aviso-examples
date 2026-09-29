"""
Download the data announced by each Extremes-DT notification from Polytope.

For every data-availability notification, the script downloads the
corresponding data and saves it to a local directory. It performs no
regridding or plotting: it is the minimal pipeline from a notification to a
file on disk.

A Polytope feature extraction downloads only the 2 m temperature time series
at a single location. Feature extraction is described in
https://github.com/destination-earth-digital-twins/polytope-examples

A feature extraction returns CoverageJSON rather than GRIB, so each result is
saved as a `.covjson` file.

Requires:
  * A valid DESP token, obtained via `python desp-authentication.py` in the
    repository root. It writes both the Polytope token (`~/.polytopeapirc`)
    and the Aviso credential (`~/.config/aviso/credentials.yaml`).
  * `earthkit-data` and `polytope-client` installed.
"""

import logging
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import earthkit.data
import pyaviso

logger = logging.getLogger(__name__)

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

    logger.info("Downloading %s", out_file)

    data = earthkit.data.from_source(
        "polytope",
        "destination-earth",
        polytope_request,
        address="polytope.lumi.apps.dte.destination-earth.eu",
        stream=False,
    )

    # earthkit-data keeps the downloaded CoverageJSON at data.path
    shutil.copyfile(data.path, out_path)
    logger.info("Saved %s (%.1f KiB)", out_path, out_path.stat().st_size / 1024)


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Start listening and download data for each notification."""
    # Progress of this script at INFO; other libraries keep the default
    # WARNING level.
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logger.setLevel(logging.INFO)
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
                except Exception:
                    # A failed download (Polytope, network or file system)
                    # skips that notification only; the listener continues.
                    # The traceback shows the cause.
                    logger.exception("Skipped notification #%s", notification.sequence)
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
