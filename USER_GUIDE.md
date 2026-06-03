# Aviso User Guide — Destination Earth Digital Twin Data Notifications

This guide describes how to use **Aviso** to receive real‑time and historical
notifications about the availability of **Destination Earth (DestinE) Digital
Twin** data, with a focus on the **Extremes Digital Twin (Extremes‑DT)**.

It complements the [`README.md`](README.md) of this repository and the upstream
[pyaviso documentation](https://pyaviso.readthedocs.io/en/latest/).

---

## Table of Contents

- [Aviso User Guide — Destination Earth Digital Twin Data Notifications](#aviso-user-guide--destination-earth-digital-twin-data-notifications)
  - [Table of Contents](#table-of-contents)
  - [1. What is Aviso?](#1-what-is-aviso)
  - [2. Aviso in the Destination Earth context](#2-aviso-in-the-destination-earth-context)
  - [3. Requirements](#3-requirements)
  - [4. Installation](#4-installation)
  - [3. Service endpoint and connectivity](#3-service-endpoint-and-connectivity)
  - [5. Core concepts](#5-core-concepts)
    - [5.1 Listener](#51-listener)
    - [5.2 Event](#52-event)
    - [5.3 Request keys (MARS‑like)](#53-request-keys-marslike)
    - [5.4 Triggers](#54-triggers)
    - [5.5 Notification payload](#55-notification-payload)
  - [6. Catch‑up and historical replay](#6-catchup-and-historical-replay)
    - [6.1 `from_date` is NOT a forecast base time](#61-from_date-is-not-a-forecast-base-time)
  - [7. Scope: Extremes Digital Twin only](#7-scope-extremes-digital-twin-only)
  - [8. Examples in this repository](#8-examples-in-this-repository)
  - [9. Quotas, throttling and best practices](#9-quotas-throttling-and-best-practices)
  - [10. Troubleshooting](#10-troubleshooting)
  - [11. References](#11-references)

---

## 1. What is Aviso?

[Aviso](https://github.com/ecmwf/aviso) is an open‑source software developed by
**ECMWF** that notifies time‑critical events across HPC and cloud systems,
enabling event‑driven workflows that span multiple domains.

In short, Aviso lets you:

- **Define events** you want to be notified about (e.g. "a new forecast step is
  available").
- **Define triggers** to execute when a matching notification is received
  (print, log, run a shell command, POST a CloudEvent, run a Python function).
- **Send and receive notifications** in near real time.


---

## 2. Aviso in the Destination Earth context

**Aviso is the mechanism that informs users
the moment a new piece of DT data becomes available**, so that downstream
workflows (post‑processing, visualization, model coupling, alerting) can react
immediately instead of polling.

Aviso sofware is developed by ECMWF and is used on various internal workflows,
therefore, a lot of the current documentation is tailored to internal user.
Since Aviso is also available throught the Destination Earth initiative, we have
compiled this user documentation and examples, which is tailored to Destine use.
Please do not refer to broader aviso documentation and examples since this is
not going to work in the scope of destination earth.

> **Important scope note.**
> Although Digital Twin data is produced on various EuroHPCs (Mare Nostrum, Lumi,
> Leonardo), the current Aviso server is currently only deployed on the
> **LUMI Databridge**, and only exposes data‑availability notifications for the
> **Extremes Digital Twins**.
> Climate DT data is currently not surfaced through Aviso.
> See [Section 7](#7-scope-extremes-digital-twin-only).

---

## 3. Requirements 

In order to use Aviso for Destine, users have to create
an account in the Destination Earth Platform and apply
for upgraded access. For more details, please visit https://platform.destine.eu/support-pages/access-policy/

Once access is granted, you need to authenticate using the [`desp-authentication.py`]. When you run the script, it will prompt you for your Destination Earth username and password (the same credentials you used to register on the platform).

After successful authentication, the script retrieves a long-living access token from the Destination Earth Service Platform (DESP) and stores it in a file named `.polytopeapirc` in your home directory. As long as this file exists, re-authentication is not necessary.

## 4. Installation
Python ≥ 3.6 is required.

In order to install all required libraries to run these
examples simply install our requirements.txt file
```bash
pip install -r requirements.txt
```
For a minimal installation
```bash
pip install pyaviso
```


---


## 3. Service endpoint and connectivity

| Setting              | Value                                                |
| -------------------- | ---------------------------------------------------- |
| Host                 | `aviso.lumi.apps.dte.destination-earth.eu`           |
| Port                 | `443` (HTTPS)                                        |
| Authentication       | None (currently; DESP auth support is planned)       |
| Notification topic   | `/de/data/`                                          |

Connectivity check:

```bash
curl -v https://aviso.lumi.apps.dte.destination-earth.eu
```

If you are behind a corporate proxy / firewall, ensure outbound TCP 443 to the
host above is allowed.

The matching Polytope data endpoint used by the Earthkit example is:

```
polytope.lumi.apps.dte.destination-earth.eu
```


---


## 5. Core concepts

### 5.1 Listener

A listener is a Python object that tells Aviso:

1. **what** event to subscribe to (`event`),
2. **which** notifications to keep (`request` — a filter dictionary),
3. **what** to do when a matching notification arrives (`triggers`).

In Python:

```python
listener = {
    "event": "data",
    "request": { ... },        # filter
    "triggers": [{...}, ...],  # one or more triggers
}
listeners_config = {"listeners": [listener]}
```

### 5.2 Event

For DestinE DT data the event is always:

```python
LISTENER_EVENT = "data"
```

(The `pyaviso` schema also defines `mars` and `dissemination` events, used in
the ECMWF operational context; they are **not** what you want for DT data.)

### 5.3 Request keys (MARS‑like)

The `request` dictionary uses keys borrowed from the MARS language. Aviso
publishes notifications whose metadata matches **every** key/value pair you
specify. The fewer keys you provide, the broader your subscription.

Keys commonly relevant to Extremes‑DT:

| Key       | Typical value                              | Meaning                                                                |
| --------- | ------------------------------------------ | ---------------------------------------------------------------------- |
| `class`   | `"d1"`                                     | Destination Earth class.                                               |
| `expver`  | `"0001"`                                   | Experiment version (operational).                                      |
| `stream`  | `"oper"`, `"wave"`                         | Stream of data.                                                        |
| `type`    | `"fc"`                                     | Forecast.                                                              |
| `levtype` | `"sfc"`, `"pl"`, `"sol"`                   | Level type (surface, pressure levels, soil…).                          |
| `date`    | `"YYYYMMDD"`                               | Forecast **base** date.                                                |
| `time`    | `"0000"`, `"1200"`                         | Forecast **base** time.                                                |
| `step`    | int or list, e.g. `[0, 3, 6, 9, 12]`       | Forecast step in hours.                                                |

Each value may be a single value or a list — for example
`"step": [0, 3, 6, 9, 12, 15, 18, 21, 24]` matches any of those steps.

### 5.4 Triggers

Triggers are what Aviso does when a notification matches. Multiple triggers per
listener are allowed; each runs as an independent process.

| Type       | Use case                                                            |
| ---------- | ------------------------------------------------------------------- |
| `echo`     | Print to stdout. Simplest, good for testing.                        |
| `log`      | Append to a log file.                                               |
| `command`  | Run a shell command; placeholders like `${request.step}` are expanded. |
| `post`     | Forward the notification as a [CloudEvent](https://cloudevents.io/) over HTTP or AWS SNS. |
| `function` | Call a Python function (used by the Earthkit example).              |

Example minimal Python triggers:

```python
# Echo
trigger = {"type": "echo"}

# Log
trigger = {"type": "log", "path": "aviso.log"}

# Shell command (with parameter substitution)
trigger = {
    "type": "command",
    "command": "./process.sh --date ${request.date} --step ${request.step}",
}

# Python function
def on_notification(n): ...
trigger = {"type": "function", "function": on_notification}
```

### 5.5 Notification payload

The dictionary passed to a `function` trigger (and the JSON sent by `post`) has
this shape:

```python
{
    "event": "data",
    "request": {
        "class":   "d1",
        "dataset": "extremes-dt",
        "expver":  "0001",
        "stream":  "oper",
        "type":    "fc",
        "levtype": "sfc",
        "date":    "20251104",
        "time":    "0000",
        "step":    "6",
        # …possibly more keys depending on the producer
    },
    # "location" / "payload" fields may also be present
}
```

In a `function` trigger you typically use the values from `notification["request"]`
to construct a Polytope (or `earthkit.data`) request and download the data.

---

## 6. Catch‑up and historical replay

When you call `nm.listen(...)`, Aviso by default:

1. Checks the **last notification** received (stored locally per‑user).
2. Replays any notifications that were missed since.
3. Switches to **real‑time** listening.

This means that after a reboot or transient outage you do not lose notifications.
The very first time you run a listener, there is no recorded state, so no catch‑up
happens.

You can explicitly request a starting point with `from_date`:

```python
nm.listen(
    listeners=listeners_config,
    from_date=datetime(2025, 11, 4),
    config=config,
)
```

A second optional `to_date` parameter bounds the replay; if set, Aviso terminates
once the historical window has been processed (otherwise it continues into
real‑time).

### 6.1 `from_date` is NOT a forecast base time

> **Common pitfall.** `from_date` is the **wall‑clock time at which the
> notification was published on the Aviso server** — i.e. the moment the data
> producer announced "this product is now available". It is **not** the forecast
> base time (`date` + `time` keys inside the request).
>
> A notification for the forecast initialized at `2025‑11‑04 00 UTC` step `120`
> is published several hours **after** `2025‑11‑04 00 UTC`, when that step has
> actually been produced. So:
>
> - If you want to replay every notification announcing data for the
>   `2025‑11‑04 00 UTC` cycle, set `from_date` to a time **before** the cycle
>   started running (e.g. `datetime(2025, 11, 3)`), and filter on
>   `"date": "20251104", "time": "0000"` inside the `request`.
> - Setting `from_date=datetime(2025, 11, 4)` will pick up only notifications
>   **published** from that moment on, which may exclude early steps and
>   include notifications for forecasts whose base time is **before**
>   `2025‑11‑04`.
>
> When in doubt, use a `from_date` clearly earlier than the forecast base time
> you care about and let the `request` filter do the selection.

---

## 7. Scope: Extremes Digital Twin only

The notifications surfaced through `aviso.lumi.apps.dte.destination-earth.eu`
on the topic used by these examples concern the **Extremes Digital Twin**:

- `class: d1`
- `dataset: extremes-dt`
- `expver: 0001`
- `stream: oper` (and `wave` for the wave component)
- 4 km global resolution; operational production began on **2023‑12‑11**.

Notifications for the **Climate DT** are produced at a different cadence and
are not part of this real‑time data‑availability stream. Trying to subscribe
with e.g. `dataset: climate-dt` against this endpoint will simply yield no
matches.

Use the [Extremes DT Data Portfolio](https://confluence.ecmwf.int/display/DDCZ/Extremes+DT+data+catalogue) to identify which
variables, levels and steps are produced for Extremes‑DT before constructing
your request filter.

---

## 8. Examples in this repository

| Script                                                                                   | What it shows                                                                |
| ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| [`aviso-extremes-dt.py`](aviso-extremes-dt.py)                                           | Minimal real‑time listener with the `echo` trigger.                          |
| [`aviso-extremes-dt-from-time.py`](aviso-extremes-dt-from-time.py)                       | Same listener, replaying from a given publish time (`from_date`).            |
| [`aviso-extremes-dt-earthkit-example.py`](aviso-extremes-dt-earthkit-example.py)         | End‑to‑end workflow: notification → Polytope download → regrid → plot.       |
| [`examples/aviso-extremes-dt-log.py`](examples/aviso-extremes-dt-log.py)                 | Persist every notification to a structured JSON‑lines log file.              |
| [`examples/aviso-extremes-dt-multi-listener.py`](examples/aviso-extremes-dt-multi-listener.py) | Two listeners with different filters (surface vs. wave) and different actions. |
| [`examples/aviso-extremes-dt-replay-window.py`](examples/aviso-extremes-dt-replay-window.py) | Replay a bounded historical window (`from_date` + `to_date`) and exit.       |
| [`examples/aviso-extremes-dt-polytope-download.py`](examples/aviso-extremes-dt-polytope-download.py) | Download GRIB to disk for every matching step (no plotting).                 |
| [`desp-authentication.py`](desp-authentication.py)                                       | Obtain a DESP offline token for Polytope (`~/.polytopeapirc`).               |

---

## 9. Quotas, throttling and best practices

- **Rate limit:** up to **50 requests/second** to the Aviso server (subject to
  change under load).
- **Concurrent operations:** currently unlimited, but be considerate.
- Use the **narrowest request filter you can** (`stream`, `levtype`, `step`) to avoid waking up your trigger for irrelevant notifications.
- In a `function` trigger, **do not block** the main thread with multi‑minute
  work. Hand off to a queue / worker pool (e.g. `concurrent.futures`, Celery,
  AWS SNS via the `post` trigger).
- If your trigger downloads from Polytope, be aware that **each** notification
  may correspond to one forecast step — your download volume scales with how
  broad your filter is.
- For production deployments where you do not want catch‑up replay, run with
  `aviso listen --now` (CLI) to reset state and listen only to new
  notifications.

---

## 10. Troubleshooting

| Symptom                                                          | Likely cause / fix                                                                                  |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Script prints `Listening to /de/data/ …` and nothing else        | Filter is correct but no matching data has been produced since you started listening. Try a `from_date` in the past. |
| `ConnectionError` / TLS errors                                   | Outbound 443 to `aviso.lumi.apps.dte.destination-earth.eu` is blocked by your network.              |
| Notifications received but Polytope download fails with 401/403  | Refresh the DESP token via `python desp-authentication.py`.                                         |
| You replay from `from_date` but receive far fewer events than expected | `from_date` filters by **publish time**, not forecast base time — see [§6.1](#61-from_date-is-not-a-forecast-base-time). |
| Catch‑up replays the same notifications every restart            | The local state file is missing or wiped — check the user config (default under `~/aviso/`).       |

---

## 11. References

- pyaviso documentation: <https://pyaviso.readthedocs.io/en/latest/>
- Aviso source: <https://github.com/ecmwf/aviso>
- Destination Earth: <https://destination-earth.eu/>
- DestinE / ECMWF Digital Twin Engine: <https://destine.ecmwf.int/>
- Polytope client: <https://github.com/ecmwf/polytope-client>
- Earthkit: <https://earthkit.readthedocs.io/>
- CloudEvents spec (used by `post` trigger): <https://cloudevents.io/>
