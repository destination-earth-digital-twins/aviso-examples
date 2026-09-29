"""
Run several listeners with different filters in one process.

This example defines two listeners:
1. Surface forecast products (oper stream), processed by a Python function.
2. Wave forecast products (wave stream), printed by the built-in echo trigger.

`listen_many()` opens both listeners on one client and processes their
notifications in a single loop, one at a time and in arrival order. It is the
pyaviso 2 equivalent of passing a list of listeners to pyaviso 1.
"""

import sys
from datetime import datetime, timedelta, timezone

import pyaviso
from pyaviso import Trigger

# ============================================================================
# CONFIGURATION
# ============================================================================

# Aviso server for pyaviso 2. The credential is found automatically in
# ~/.config/aviso/credentials.yaml; run ../desp-authentication.py once to
# write it.
AVISO_URL = "https://aviso2.lumi.apps.dte.destination-earth.eu"

# Replay start point: publication time (UTC), not forecast base time
FROM_DATE = datetime.now(timezone.utc) - timedelta(days=14)

# Event type (always "data" for Extremes-DT)
EVENT_TYPE = "data"

SURFACE_FILTER = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    "step": {"in": [0, 3, 6, 9, 12, 15, 18, 21, 24]},
}

# The step filter keeps a 14-day replay of every wave step under the server's
# replay limit (see README section 7.2).
WAVE_FILTER = {
    "class": "d1",
    "expver": "0001",
    "stream": "wave",
    "type": "fc",
    "step": {"in": [0, 6, 12, 18, 24]},
}

# ============================================================================
# PROCESSING
# ============================================================================


def on_surface(notification):
    """Process surface forecast notifications."""
    i = notification.identifier
    print(
        "[surface] base={date} {time}Z step={step} ready".format(
            date=i.get("date"), time=i.get("time"), step=i.get("step")
        ),
        flush=True,
    )


# ============================================================================
# LISTENERS
# ============================================================================

LISTENERS = {
    "surface": {
        "event_type": EVENT_TYPE,
        "filter": SURFACE_FILTER,
        "triggers": [Trigger.function(on_surface)],
    },
    "wave": {
        "event_type": EVENT_TYPE,
        "filter": WAVE_FILTER,
        "triggers": [Trigger.echo()],
    },
}

# ============================================================================
# MAIN
# ============================================================================


def main():
    """Start listening for both surface and wave notifications."""
    start = FROM_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        client = pyaviso.AvisoClient(base_url=AVISO_URL)
        # The echo trigger writes to standard output directly. Flushing keeps
        # these lines in order with its output when the output is redirected.
        print(client.config, flush=True)
        print(f"Listening for {EVENT_TYPE} notifications published from {start} ...")
        print("Stop with Ctrl+C.\n", flush=True)
        # run() processes notifications until it is interrupted. If one
        # listener fails, both are closed and the error is raised, with the
        # listener name at the start of its message.
        client.listen_many(LISTENERS, start_from=start).run()
    except KeyboardInterrupt:
        print("\nListener stopped.")
    except pyaviso.HistoryGapError as e:
        if e.reason == "replay_limit_reached":
            sys.exit(
                f"Replay stopped for listener '{e.listener}': more notifications "
                "match than the server replays at once. Narrow its filter or "
                "start later."
            )
        sys.exit(f"Aviso error: {e}")
    except pyaviso.AvisoError as e:
        sys.exit(f"Aviso error: {e}")


if __name__ == "__main__":
    main()
