"""
Resume after a restart: catch up on what was published while the script was
stopped, then continue live.

pyaviso 1 did this by default. pyaviso 2 does it when the client is given a
state store: the client saves its position (a sequence number) in a local
file, and the next run with the same server, event type and filter continues
after it.

On the very first run there is no saved position, so this script starts from
FIRST_RUN_FROM instead. Stop it with Ctrl+C and start it again: it picks up
where it stopped. The last notification before a stop may be delivered again,
so make processing safe to repeat.

A saved position records what was received, not what your code finished
processing. If that difference matters, track completed work separately.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pyaviso

# ============================================================================
# CONFIGURATION
# ============================================================================

# Aviso server for pyaviso 2. The credential is found automatically in
# ~/.config/aviso/credentials.yaml; run ../desp-authentication.py once to
# write it.
AVISO_URL = "https://aviso2.lumi.apps.dte.destination-earth.eu"

# Where the position is saved. Keep it on a local disk (not NFS). Delete the
# file to start over from FIRST_RUN_FROM.
STATE_PATH = Path.home() / ".config" / "aviso" / "extremes-dt-resume-state.json"

# Where the first run starts: publication time (UTC)
FIRST_RUN_FROM = datetime.now(timezone.utc) - timedelta(days=1)

# Event type (always "data" for Extremes-DT)
EVENT_TYPE = "data"

# Filter: only notifications matching ALL keys are delivered. The saved
# position belongs to this filter: after changing it, delete STATE_PATH so the
# next run replays from FIRST_RUN_FROM rather than starting at the live edge.
FILTER = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "type": "fc",
    "levtype": "sfc",
    "step": {"in": [0, 6, 12, 18, 24]},
}

# ============================================================================
# PROCESSING
# ============================================================================


def process(notification):
    """Handle one notification. Must be safe to run twice for the same one."""
    i = notification.identifier
    print(
        f"#{notification.sequence}: base={i.get('date')} {i.get('time')}Z "
        f"step={i.get('step')}"
    )


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Catch up from the saved position (or FIRST_RUN_FROM), then listen live."""
    first_run = not STATE_PATH.exists()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # An explicit start_from overrides the saved position, so it is given
    # only when there is nothing saved yet.
    start = FIRST_RUN_FROM.strftime("%Y-%m-%dT%H:%M:%SZ") if first_run else None
    try:
        client = pyaviso.AvisoClient(
            base_url=AVISO_URL,
            state_store=pyaviso.JsonFileStore(STATE_PATH),
        )
        print(client.config)
        if first_run:
            print(f"First run: replaying notifications published from {start} ...")
        else:
            print(f"Resuming from the position saved in {STATE_PATH} ...")
        print("Stop with Ctrl+C, then run again to resume.\n")
        with client.listen(
            EVENT_TYPE, filter=FILTER, start_from=start
        ) as notifications:
            for notification in notifications:
                process(notification)
    except KeyboardInterrupt:
        print(f"\nListener stopped. Position saved in {STATE_PATH}")
    except pyaviso.HistoryGapError as e:
        if e.reason == "replay_limit_reached":
            # The position is saved as notifications arrive, so the next run
            # continues after the last one this run received.
            sys.exit(
                "Replay stopped: more was published since the saved position "
                "than the server replays at once. Run again to continue."
            )
        sys.exit(f"Aviso error: {e}")
    except pyaviso.AvisoError as e:
        sys.exit(f"Aviso error: {e}")


if __name__ == "__main__":
    main()
