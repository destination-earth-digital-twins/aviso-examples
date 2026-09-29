"""
Persist every Extremes-DT data-availability notification to a JSON-lines log
file using the built-in `log` trigger.

The trigger appends each notification as one JSON document per line to
`aviso-extremes-dt-log_<timestamp>.jsonl`, before the notification reaches the
loop below. If the file cannot be written, the listener stops with an error
rather than dropping the notification silently.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
FROM_DATE = datetime.now(timezone.utc) - timedelta(days=5)

# Output file with timestamp to avoid overwrites
SCRIPT_NAME = Path(__file__).stem
RUN_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
LOG_PATH = Path(f"{SCRIPT_NAME}_{RUN_TIMESTAMP}.jsonl")

# Event type (always "data" for Extremes-DT)
EVENT_TYPE = "data"

# Filter: narrow to surface forecast products of Extremes DT
FILTER = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    "step": {"in": [0, 3, 6, 9, 12, 15, 18, 21, 24]},
}

# ============================================================================
# MAIN
# ============================================================================


def main():
    """Listen for notifications and append each to a JSON-lines log file."""
    start = FROM_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        client = pyaviso.AvisoClient(base_url=AVISO_URL)
        print(client.config)
        print(f"Logging Extremes-DT notifications to {LOG_PATH.resolve()}")
        print("Stop with Ctrl+C.\n")
        with client.listen(
            EVENT_TYPE,
            filter=FILTER,
            start_from=start,
            triggers=[Trigger.log(LOG_PATH)],
        ) as notifications:
            for notification in notifications:
                i = notification.identifier
                print(
                    f"logged #{notification.sequence}: base={i.get('date')} "
                    f"{i.get('time')}Z step={i.get('step')}"
                )
    except KeyboardInterrupt:
        print(f"\nLogging stopped. Output saved to {LOG_PATH.resolve()}")
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
