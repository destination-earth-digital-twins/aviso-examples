"""
Minimal real-time listener for Extremes-DT data-availability notifications.

This script demonstrates the simplest listening pattern:
- Connect to the Aviso server with the credential written by
  `../desp-authentication.py`.
- Define a filter for Extremes-DT products.
- Print each matching notification as it arrives.
- Continue listening until interrupted (Ctrl+C).
"""

import sys

import pyaviso

# ============================================================================
# CONFIGURATION
# ============================================================================

# Aviso server for pyaviso 2. The credential is found automatically in
# ~/.config/aviso/credentials.yaml; run ../desp-authentication.py once to
# write it.
AVISO_URL = "https://aviso2.lumi.apps.dte.destination-earth.eu"

# Event type (always "data" for Extremes-DT)
EVENT_TYPE = "data"

# Filter: only notifications matching ALL keys are delivered. Alternatives for
# one key are written as {"in": [...]}.
FILTER = {
    "class": "d1",
    "expver": "0001",
    "stream": "wave",
    "step": {"in": [1, 2, 3]},
    "levtype": "sfc",
    "type": "fc",
}

# ============================================================================
# MAIN
# ============================================================================


def main():
    """Start listening for real-time Extremes-DT data notifications."""
    try:
        client = pyaviso.AvisoClient(base_url=AVISO_URL)
        # Which server and which credential the client uses, and where each
        # came from. The token itself is never shown.
        print(client.config)
        print(f"Listening for new {EVENT_TYPE} notifications ...")
        print("Stop with Ctrl+C.\n")
        with client.listen(EVENT_TYPE, filter=FILTER) as notifications:
            for notification in notifications:
                print(notification)
    except KeyboardInterrupt:
        print("\nListener stopped.")
    except pyaviso.AvisoError as e:
        sys.exit(f"Aviso error: {e}")


if __name__ == "__main__":
    main()
