"""
Replay notifications from a past publish time, then continue listening live.

Unlike the real-time listener, this script:
- Replays notifications published from FROM_DATE onward.
- Catches up any missed notifications.
- Then continues listening to new notifications.

This is useful for recovery after outages or to backfill initial setup. To
resume automatically from where the last run stopped, see
`aviso-extremes-dt-resume.py`.
"""

import sys
from datetime import datetime, timedelta, timezone

import pyaviso

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
    """Print the received notification."""
    print(notification)


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Replay from FROM_DATE, then continue listening for new notifications."""
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
                do_something(notification)
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
