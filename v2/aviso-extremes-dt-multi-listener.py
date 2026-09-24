"""
Run several listeners with different filters in one process.

This example shows two parallel subscriptions:
1. Surface forecast products (oper stream) -> a Python function.
2. Wave forecast products (wave stream) -> the built-in echo trigger.

pyaviso 2 has no listener list: each subscription is one `listen()` call. The
asynchronous client runs them side by side in a single thread, which is the
recommended pattern for reacting differently to different Extremes-DT
products.
"""

import asyncio
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
        )
    )


# ============================================================================
# LISTENERS
# ============================================================================


async def surface_listener(client, start):
    """Call on_surface for every surface forecast notification."""
    async with client.listen(
        EVENT_TYPE, filter=SURFACE_FILTER, start_from=start
    ) as notifications:
        async for notification in notifications:
            on_surface(notification)


async def wave_listener(client, start):
    """Print every wave forecast notification with the echo trigger."""
    async with client.listen(
        EVENT_TYPE, filter=WAVE_FILTER, start_from=start, triggers=[Trigger.echo()]
    ) as notifications:
        async for _ in notifications:
            pass  # the echo trigger has already printed it


async def run():
    client = pyaviso.AsyncAvisoClient(base_url=AVISO_URL)
    print(client.config)
    start = FROM_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Listening for {EVENT_TYPE} notifications published from {start} ...")
    print("Stop with Ctrl+C.\n")
    # If either listener fails, gather raises its error and asyncio.run then
    # cancels the other one, so a broken subscription never half-runs silently.
    await asyncio.gather(
        surface_listener(client, start),
        wave_listener(client, start),
    )


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Start listening for both surface and wave notifications."""
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nListener stopped.")
    except pyaviso.HistoryGapError as e:
        if e.reason == "replay_limit_reached":
            sys.exit(
                "Replay stopped: more notifications match than the server "
                "replays at once. Narrow the filters or start later."
            )
        sys.exit(f"Aviso error: {e}")
    except pyaviso.AvisoError as e:
        sys.exit(f"Aviso error: {e}")


if __name__ == "__main__":
    main()
