"""
Replay Extremes-DT notifications inside a bounded historical window and exit.

Unlike `aviso-extremes-dt-from-time.py`, which catches up from a given moment
and then keeps listening, this example replays history only and stops at
TO_DATE.

This is the right pattern when you want to:

  * Rebuild a local index of past notifications,
  * Test processing code deterministically against real notifications,
  * Backfill a downstream system without subscribing to the live stream.

`until` ends the replay with the last notification published at or before
TO_DATE, and the loop then finishes on its own. Both ends of the window are
inclusive.

IMPORTANT: FROM_DATE/TO_DATE refer to the time the notification was
PUBLISHED on the Aviso server (i.e. when the producer announced the data was
available). They are NOT the forecast base time. To target forecasts
initialised at a specific cycle, use `date`/`time` in the filter and set
the window generously around the production wall-clock.
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

# Publication-time window (UTC). The server replays at most 10,000
# notifications per request, so keep the window short for broad filters.
# Whole seconds, so the window printed is exactly the window requested.
TO_DATE = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=1)
FROM_DATE = TO_DATE - timedelta(days=1)

# Event type (always "data" for Extremes-DT)
EVENT_TYPE = "data"

# Filter: only notifications matching ALL keys are delivered
FILTER = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    # Optionally narrow to a specific forecast cycle:
    # "date": "20251104",
    # "time": "0000",
}

# ============================================================================
# PROCESSING
# ============================================================================


def count_and_print(notification, count):
    """Display each notification with a running count."""
    i = notification.identifier
    print(
        f"[{count:04d}] base={i.get('date')} {i.get('time')}Z "
        f"step={i.get('step')} stream={i.get('stream')}"
    )


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Replay a bounded historical window and exit."""
    start = FROM_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = TO_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    count = 0
    try:
        client = pyaviso.AvisoClient(base_url=AVISO_URL)
        print(client.config)
        print("Replaying notifications published between:")
        print(f"  From: {start}")
        print(f"  To:   {end}")
        print(f"Filter: {FILTER}\n")
        with client.listen(
            EVENT_TYPE, filter=FILTER, start_from=start, until=end
        ) as notifications:
            for notification in notifications:
                count += 1
                count_and_print(notification, count)
        print(f"\nReplay complete: {count} notifications.")
    except KeyboardInterrupt:
        print(f"\nReplay stopped after {count} notifications.")
    except pyaviso.HistoryGapError as e:
        if e.reason == "replay_limit_reached":
            sys.exit(
                "Replay stopped: more notifications match than the server "
                "replays at once. Narrow FILTER or shorten the window."
            )
        sys.exit(f"Aviso error: {e}")
    except pyaviso.AvisoError as e:
        sys.exit(f"Aviso error: {e}")


if __name__ == "__main__":
    main()
