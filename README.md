# Aviso for Destination Earth — Extremes Digital Twin <!-- omit from toc -->

This repository provides documentation and example scripts for using **Aviso**
to receive data-availability notifications for **Destination Earth (DestinE)
Digital Twin** data, with a focus on the **Extremes Digital Twin (Extremes-DT)**.

## Table of Contents <!-- omit from toc -->

- [1. What is Aviso?](#1-what-is-aviso)
- [2. Aviso in the Destination Earth Context](#2-aviso-in-the-destination-earth-context)
- [3. Requirements and Access](#3-requirements-and-access)
- [4. Installation](#4-installation)
- [5. Service Endpoints and Connectivity](#5-service-endpoints-and-connectivity)
- [6. Running the Examples](#6-running-the-examples)
- [7. Core Concepts](#7-core-concepts)
  - [7.1 Listener](#71-listener)
  - [7.2 Event](#72-event)
  - [7.3 Request Keys (MARS-like)](#73-request-keys-mars-like)
  - [7.4 Triggers](#74-triggers)
  - [7.5 Notification Payload](#75-notification-payload)
- [8. Catch-up and Historical Replay](#8-catch-up-and-historical-replay)
  - [8.1 `from_date` and `to_date` on listerner do NOT refer to a Forecast Base Time](#81-from_date-and-to_date-on-listerner-do-not-refer-to-a-forecast-base-time)
- [9. Scope: Extremes Digital Twin Only](#9-scope-extremes-digital-twin-only)
- [10. Examples in this Repository](#10-examples-in-this-repository)
- [11. Quotas, Throttling, and Best Practices](#11-quotas-throttling-and-best-practices)
- [12. Troubleshooting](#12-troubleshooting)
- [13. References](#13-references)

---

## 1. What is Aviso?

[Aviso](https://github.com/ecmwf/aviso) is an open-source notification system
developed by **ECMWF** that broadcasts time-critical events across HPC and cloud
systems, enabling event-driven workflows that span multiple domains.

In short, Aviso lets you:

- **Subscribe to events** you care about (e.g. "a new forecast step is ready").
- **Define triggers** that execute when a matching notification arrives — print,
  log, run a shell command, POST a CloudEvent, or call a Python function.
- **React in near real time** rather than polling for new data.

---

## 2. Aviso in the Destination Earth Context

Aviso is the mechanism that informs users the moment new forecast data becomes
available, so that downstream workflows — post-processing, visualisation, model
coupling, alerting — can react immediately.

Aviso is developed and used extensively at ECMWF across internal operational
workflows, so much of the upstream documentation is aimed at ECMWF-internal
users. **The examples and documentation in this repository are tailored
specifically to Destination Earth.** Generic pyaviso examples from the upstream
docs may reference events, endpoints, or authentication methods that do not
apply in the DestinE context.

> [!WARNING]
> Although Digital Twin data is produced on multiple EuroHPC systems (Mare
> Nostrum, LUMI, Leonardo), the Aviso server is currently deployed only on the
> **LUMI Databridge** and exposes notifications for the **Extremes Digital
> Twin only**. Climate DT notifications are not currently available through
> Aviso.
>
> See [Section 9](#9-scope-extremes-digital-twin-only) for details.

---

## 3. Requirements and Access

> [!NOTE]
> Listening to Aviso notifications does **not** require authentication — the
> current endpoint uses `auth_type: none`. However, downloading data via
> Polytope (used in the Earthkit example) **does** require valid DESP
> credentials.

To obtain DESP credentials:

1. Register at the [DestinE Platform](https://platform.destine.eu/).
2. Apply for upgraded access as described in the
   [access policy](https://platform.destine.eu/support-pages/access-policy/).

Once upgraded access is granted, run the [`desp-authentication.py`](desp-authentication.py) script.
It will prompt for your DestinE username and password, then retrieve a
long-lived offline token from the Destination Earth Service Platform (DESP)
and store it at `~/.polytopeapirc`. Re-authentication is only needed when that
token expires.

---

## 4. Installation

Python ≥ 3.6 is required.

Install all dependencies used in this repository:

```bash
pip install -r requirements.txt
```

For a minimal installation (listener only, no data download or plotting):

```bash
pip install pyaviso
```

---

## 5. Service Endpoints and Connectivity

| Setting                  | Value                                                    |
| ------------------------ | -------------------------------------------------------- |
| Aviso host               | `aviso.lumi.apps.dte.destination-earth.eu`               |
| Port                     | `443` (HTTPS)                                            |
| Polytope host (data)     | `polytope.lumi.apps.dte.destination-earth.eu`            |

Verify connectivity before running the examples:

```bash
curl -v https://aviso.lumi.apps.dte.destination-earth.eu
```

If you are on a corporate or institutional network, ensure outbound TCP 443 to
the Aviso host is permitted by your firewall or proxy.

---

## 6. Running the Examples

All scripts can be run directly from the repository root.

**Real-time listener (echo trigger):**

```bash
python3 aviso-extremes-dt.py
```

**Replay from a past publish time, then continue live:**

```bash
python3 aviso-extremes-dt-from-time.py
```

**End-to-end Earthkit/Polytope workflow:**

```bash
python3 aviso-extremes-dt-earthkit-example.py
```

On startup you should see output similar to:

```text
loaded config:
{'auth_type': 'none',
 'configuration_engine': {'host': 'aviso.lumi.apps.dte.destination-earth.eu',
                          'https': True,
                          'port': 443},
 'notification_engine': {'host': 'aviso.lumi.apps.dte.destination-earth.eu',
                         'https': True,
                         'port': 443},
 'remote_schema': True,
 'schema_parser': 'generic'}
Listening to /de/data/ at aviso.lumi.apps.dte.destination-earth.eu:443...
```

Notifications matching your filter will be printed to stdout as they arrive.
Stop with `Ctrl + C`.

> [!IMPORTANT]
> On every startup, Aviso checks the last notification it received and replays
> any that were missed before switching to real-time listening. On the very
> first run there is no prior state, so no historical notifications are
> returned. This catch-up behaviour ensures no notifications are lost across
> restarts or outages. See [Section 8](#8-catch-up-and-historical-replay) for
> full details.

---

## 7. Core Concepts

### 7.1 Listener

A listener is a Python dictionary that tells Aviso what to watch for and what to
do when a match is found. It has three required parts:

1. **`event`** — the kind of event to listen for.
2. **`request`** — a filter dictionary; only notifications whose metadata
   matches all keys are delivered.
3. **`triggers`** — one or more actions to execute per matching notification.

```python
listener = {
    "event": "data",
    "request": { ... },        # filter keys
    "triggers": [{...}, ...],  # one or more triggers
}
listeners_config = {"listeners": [listener]}
```

### 7.2 Event

For DestinE Digital Twin data, the event is always:

```python
LISTENER_EVENT = "data"
```

The `pyaviso` schema also defines `mars` and `dissemination` events used in
ECMWF operational contexts — these are **not** relevant for DT data.

### 7.3 Request Keys (MARS-like)

The `request` dictionary uses keys from the MARS language. A notification is
delivered only when **every** specified key matches. The fewer keys you include,
the broader the subscription.

| Key       | Typical value             | Meaning                                         |
| --------- | ------------------------- | ----------------------------------------------- |
| `class`   | `"d1"`                    | Destination Earth class                         |
| `expver`  | `"0001"`                  | Experiment version (operational)                |
| `stream`  | `"oper"`, `"wave"`        | Data stream                                     |
| `type`    | `"fc"`                    | Forecast                                        |
| `levtype` | `"sfc"`, `"pl"`, `"sol"`  | Level type (surface, pressure levels, soil)     |
| `date`    | `"YYYYMMDD"`              | Forecast base date                              |
| `time`    | `"0000"`, `"1200"`        | Forecast base time                              |
| `step`    | `0`, `[0, 3, 6, ...]`     | Forecast lead time in hours                     |

Each value can be a scalar or a list — for example,
`"step": [0, 3, 6, 9, 12, 15, 18, 21, 24]` matches any of those steps.

### 7.4 Triggers

Triggers define what happens when a notification matches. Multiple triggers per
listener are supported; each runs as an independent process.

| Type       | Use case                                                                         |
| ---------- | -------------------------------------------------------------------------------- |
| `echo`     | Print to stdout — simplest, good for testing.                                    |
| `log`      | Append notifications to a log file.                                              |
| `command`  | Run a shell command; supports substitutions like `${request.step}`.              |
| `post`     | Forward as a [CloudEvent](https://cloudevents.io/) over HTTP or AWS SNS.         |
| `function` | Call a Python function directly — used in the Earthkit example.                  |

Example trigger definitions:

```python
# Echo (no extra config)
trigger = {"type": "echo"}

# Log to file
trigger = {"type": "log", "path": "aviso.log"}

# Shell command with request field substitution
trigger = {
    "type": "command",
    "command": "./process.sh --date ${request.date} --step ${request.step}",
}

# Python callback
def on_notification(notification): ...
trigger = {"type": "function", "function": on_notification}
```

### 7.5 Notification Payload

The dictionary received by a `function` trigger (and sent by the `post` trigger
as JSON) looks like this:

```python
{
    "event": "data",
    "request": {
        "class":   "d1",
        "expver":  "0001",
        "stream":  "oper",
        "type":    "fc",
        "levtype": "sfc",
        "date":    "20251104",
        "time":    "0000",
        "step":    "6",
    },
}
```

In a `function` trigger, the values from `notification["request"]` are typically
used to construct a Polytope or `earthkit.data` request to retrieve the data.

---

## 8. Catch-up and Historical Replay

When `nm.listen(...)` is called, Aviso by default:

1. Checks the **last notification received** (persisted locally per user).
2. Replays any notifications missed since then.
3. Switches to **real-time** listening.

After a reboot or transient outage, no notifications are lost. On the very first
run there is no prior state, so no catch-up occurs.

To explicitly set a starting point, use `from_date`:

```python
nm.listen(
    listeners=listeners_config,
    from_date=datetime(2025, 11, 4), #optional
    to_date=datetime(2025, 11, 30), #optional
    config=config,
)
```

An optional `to_date` bounds the replay window; when set, Aviso exits after
processing the historical range instead of continuing into real-time.
> [!IMPORTANT]
> If using to_date, it must always be set to a date before current date.

### 8.1 `from_date` and `to_date` on listerner do NOT refer to a Forecast Base Time

> [!WARNING]
> `from_date` is the **wall-clock time at which the notification was published**
> on the Aviso server — i.e. when the data producer announced that a product was
> available. It is **not** the forecast base time (`date` + `time` in the
> request).
>
> Extreme-DT data is typically produced daily, with model runs completeting at around
> 8:00 UTC and the transfer of the data into the Data Bridges completing around 10:50
> UTC. However, issues on Lumi and increased queieing times can lead data to
> be produced several hours ou even days **after** this schedule.
>
> A notification for the forecast initialised at `2025-11-04 00 UTC` can be
> published several hours ou even days **after** `2025-11-04 00 UTC`, in case
> there are issues on LUMI or increased queing times.
>
> - To replay all notifications for the `2025-11-04 00 UTC` cycle, set
>   `from_date` to a time **before** the cycle started (e.g.
>   `datetime(2025, 11, 3)`) and narrow the selection using
>   `"date": "20251104", "time": "0000"` in `request`.
> - Setting `from_date=datetime(2025, 11, 4)` captures only notifications
>   **published** from that moment onward, which may miss early steps and
>   **include products from prior forecast cycles.**
>
> When in doubt, set `from_date` conservatively early and let the `request`
> filter do the selection.
>
> The same is valid for `to_date`

---

## 9. Scope: Extremes Digital Twin Only

Notifications available through the endpoint used in these examples are limited
to the **Extremes Digital Twin**:

- `class: d1`, `expver: 0001`
- `stream: oper` (and `wave` for the wave component)
- 4 km global resolution; operational production began on **2023-12-11**

Climate DT data is not available through Aviso at this time.

Consult the [Extremes DT Data Catalogue](https://confluence.ecmwf.int/display/DDCZ/Extremes+DT+data+catalogue)
to identify available variables, levels, and forecast steps before constructing
your request filter.

---

## 10. Examples in this Repository

| Script | Description |
| --- | --- |
| [`aviso-extremes-dt.py`](aviso-extremes-dt.py) | Minimal real-time listener with the `echo` trigger. |
| [`aviso-extremes-dt-from-time.py`](aviso-extremes-dt-from-time.py) | Replay from a given publish time, then continue listening live. |
| [`aviso-extremes-dt-earthkit-example.py`](aviso-extremes-dt-earthkit-example.py) | End-to-end workflow: notification → Polytope download → regrid → Europe map plot. |
| [`aviso-extremes-dt-log.py`](aviso-extremes-dt-log.py) | Persist every notification to a structured JSON-lines log file. |
| [`aviso-extremes-dt-multi-listener.py`](aviso-extremes-dt-multi-listener.py) | Two listeners in one process with different filters (surface vs. wave). |
| [`aviso-extremes-dt-replay-window.py`](aviso-extremes-dt-replay-window.py) | Replay a bounded historical window (`from_date` + `to_date`) and exit. |
| [`aviso-extremes-dt-polytope-download.py`](aviso-extremes-dt-polytope-download.py) | Download GRIB data to disk for every matching step (no plotting). |
| [`desp-authentication.py`](desp-authentication.py) | Obtain a DESP offline token and store it for Polytope access. |

---

## 11. Quotas, Throttling, and Best Practices

- **Rate limit:** up to **50 requests/second** to the Aviso server (may be
  adjusted under load).
- **Concurrent operations:** currently unlimited, but please be considerate.
- Use the **narrowest request filter** possible (`stream`, `levtype`, `step`) to
  avoid triggering on irrelevant notifications.
- In a `function` trigger, **do not block the main thread** with lengthy
  operations. Hand off work to a queue or worker pool (e.g. `concurrent.futures`,
  Celery, or use the `post` trigger to forward to an external system).
- Each notification typically corresponds to one forecast step — download volume
  scales directly with how broad your filter is.
- For production deployments that should ignore catch-up replay, run
  `aviso listen --now` (CLI) to reset the local state and listen only to new
  notifications.

---

## 12. Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| Script prints `Listening to /de/data/ …` and no notifications arrive | No matching data published since you started, or filter is too narrow. Try a `from_date` in the past. |
| `ConnectionError` / TLS errors | Outbound port 443 to `aviso.lumi.apps.dte.destination-earth.eu` is blocked by your network. |
| Polytope download fails with 401 / 403 | Refresh the DESP token by re-running `desp-authentication.py`. |
| `from_date` replay returns fewer events than expected | `from_date` is a publish time, not a forecast base time — see [§8.1](#81-from_date-is-not-a-forecast-base-time). |
| Catch-up replays the same notifications on every restart | The local state file is missing or being reset — check the Aviso config directory (default: `~/aviso/`). |

---

## 13. References

- pyaviso documentation: <https://pyaviso.readthedocs.io/en/latest/>
- Aviso source code: <https://github.com/ecmwf/aviso>
- Destination Earth: <https://destination-earth.eu/>
- DestinE / ECMWF Digital Twin Engine: <https://destine.ecmwf.int/>
- Extremes DT Data Catalogue: <https://confluence.ecmwf.int/display/DDCZ/Extremes+DT+data+catalogue>
- Polytope client: <https://github.com/ecmwf/polytope-client>
- Earthkit: <https://earthkit.readthedocs.io/>
- CloudEvents specification: <https://cloudevents.io/>
