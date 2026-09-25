"""
End-to-end Extremes-DT processing workflow: notification → data download → regrid → plot.

When a new Extremes-DT forecast becomes available, this script:
1. Receives the data-availability notification.
2. Downloads the corresponding field via Polytope.
3. Regrids to coarser resolution for faster processing.
4. Generates a map plot focused on Europe.

Requires earthkit-data, earthkit-plots, earthkit-regrid and polytope-client,
and a DESP token from `python desp-authentication.py` in the repository root.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import earthkit.data
import earthkit.plots
import earthkit.regrid
import matplotlib
import pyaviso

# Render plots to files only. No figure exists yet, so the backend can still be
# selected after earthkit-plots has imported matplotlib.
matplotlib.use("agg")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Aviso server for pyaviso 2. The credential is found automatically in
# ~/.config/aviso/credentials.yaml.
AVISO_URL = "https://aviso2.lumi.apps.dte.destination-earth.eu"

# Output directory for downloaded PNG files
OUT_DIR = Path(__file__).parent / "downloads"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Replay start point: publication time (UTC), not forecast base time
FROM_DATE = datetime.now(timezone.utc) - timedelta(days=14)

# Event type (always "data" for Extremes-DT)
EVENT_TYPE = "data"

# Filter: only notifications matching ALL keys are delivered
FILTER = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "step": {"in": [0, 3, 6, 9, 12, 15, 18, 21, 24]},
    "levtype": "sfc",
    "type": "fc",
}

# ============================================================================
# PROCESSING
# ============================================================================


def do_something(notification):
    """Download, regrid, and plot temperature data on notification."""
    print(notification)

    identifier = notification.identifier
    rdate = identifier["date"]
    rtime = identifier["time"]
    rstep = identifier["step"]

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

    # regrid to 0.1x0.1 degree
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
    chart.save(OUT_DIR / f"2t-extremes-dt-{rdate}{rtime}Z-step{rstep}.png")
    chart.show()


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Start listening for Extremes-DT notifications and process each one."""
    start = FROM_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        client = pyaviso.AvisoClient(base_url=AVISO_URL)
        print(client.config)
        print(f"Replaying notifications published from {start} ...")
        print("Stop with Ctrl+C.\n")
        with client.listen(
            EVENT_TYPE, filter=FILTER, start_from=start
        ) as notifications:
            for notification in notifications:
                try:
                    do_something(notification)
                except Exception as e:
                    # One failed download must not stop the listener.
                    print(f"Skipped #{notification.sequence}: {e}")
    except KeyboardInterrupt:
        print("\nListener stopped.")
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
