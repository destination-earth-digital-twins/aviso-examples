# Aviso for Destination Earth — Extremes Digital Twin (pyaviso 2) <!-- omit from toc -->

These examples use **pyaviso 2** and the Aviso server at
`https://aviso2.lumi.apps.dte.destination-earth.eu`. They replace the pyaviso 1
examples in [`../v1/`](../v1/), which will be decommissioned at the beginning
of 2027. The [repository README](../README.md) compares the two versions.

## Table of Contents <!-- omit from toc -->

- [1. What is Aviso?](#1-what-is-aviso)
- [2. Installation](#2-installation)
- [3. Requirements and Access](#3-requirements-and-access)
- [4. Service Endpoints and Connectivity](#4-service-endpoints-and-connectivity)
- [5. Running the Examples](#5-running-the-examples)
- [6. Core Concepts](#6-core-concepts)
  - [6.1 Client](#61-client)
  - [6.2 Event Type](#62-event-type)
  - [6.3 Filter Keys (MARS-like)](#63-filter-keys-mars-like)
  - [6.4 The Notification Object](#64-the-notification-object)
  - [6.5 Processing: the Loop and Triggers](#65-processing-the-loop-and-triggers)
  - [6.6 Several Listeners](#66-several-listeners)
- [7. Catch-up, Replay and Resume](#7-catch-up-replay-and-resume)
  - [7.1 Start Positions are Publication Times, Not Forecast Base Times](#71-start-positions-are-publication-times-not-forecast-base-times)
  - [7.2 The Replay Limit](#72-the-replay-limit)
  - [7.3 Resuming After a Restart](#73-resuming-after-a-restart)
- [8. Scope: Extremes Digital Twin Only](#8-scope-extremes-digital-twin-only)
- [9. Examples in this Folder](#9-examples-in-this-folder)
- [10. Best Practices](#10-best-practices)
- [11. Troubleshooting](#11-troubleshooting)
- [12. References](#12-references)

---

## 1. What is Aviso?

[Aviso](https://sites.ecmwf.int/docs/aviso-client/stable/) is a notification system developed by
**ECMWF** that announces time-critical events, such as "a new forecast step is
ready", so that workflows can react immediately instead of polling. For
Destination Earth it tells you the moment new Digital Twin data is available,
so post-processing, visualisation, model coupling or alerting can start at
once.

pyaviso 2 is a new client for a new server. It is not a drop-in upgrade of
pyaviso 1: listeners, filters and start positions are written differently.
Section 4 of the [repository README](../README.md#4-moving-from-v1-to-v2) maps
each pyaviso 1 construct to its pyaviso 2 equivalent.

---

## 2. Installation

Python 3.10 or newer is required. pyaviso 1 and pyaviso 2 share a package name,
so use an environment of their own:

```bash
python3 -m venv .venv-v2
source .venv-v2/bin/activate
pip install -r requirements.txt
```

For a minimal installation (listening only, no data download or plotting):

```bash
pip install "pyaviso>=2.2.2,<3" conflator lxml requests
```

The last three are for `desp-authentication.py`.

---

## 3. Requirements and Access

> [!IMPORTANT]
> Unlike pyaviso 1, pyaviso 2 needs a **DESP credential to listen**. Without
> one the server answers `401 Unauthorized`. Downloading data through Polytope
> needs the same credential.

To obtain DESP credentials:

1. Register at the [DestinE Platform](https://platform.destine.eu/).
2. Apply for upgraded access as described in the
   [access policy](https://platform.destine.eu/support-pages/access-policy/).

Once upgraded access is granted, run
[`desp-authentication.py`](../desp-authentication.py) from the repository root.
It writes the DESP offline token to `~/.polytopeapirc` for Polytope and to
`~/.config/aviso/credentials.yaml` for pyaviso 2. Every example finds the
credential there; nothing in the code names it. See
[Access and Authentication](../README.md#2-access-and-authentication) for the
script's options.

---

## 4. Service Endpoints and Connectivity

| Setting               | Value                                                   |
| --------------------- | ------------------------------------------------------- |
| Aviso server          | `https://aviso2.lumi.apps.dte.destination-earth.eu`     |
| Port                  | `443` (HTTPS)                                           |
| Polytope host (data)  | `polytope.lumi.apps.dte.destination-earth.eu`           |

Check connectivity, and see what the server offers, with its schema endpoint
(no credential needed):

```bash
curl https://aviso2.lumi.apps.dte.destination-earth.eu/api/v1/schema
```

If you are on a corporate or institutional network, make sure outbound TCP 443
to the Aviso host is allowed by your firewall or proxy.

---

## 5. Running the Examples

All scripts are run from this folder (`v2/`):

```bash
python aviso-extremes-dt.py
```

Each one first prints the connection it resolved:

```text
ResolvedConfig(
    base_url='https://aviso2.lumi.apps.dte.destination-earth.eu/' (code),
    auth="bearer"                                    (credentials file /home/you/.config/aviso/credentials.yaml),
    timeout=None                                     (default),
    heartbeat_interval=None                          (default),
    ca_bundle=[]                                     (default),
    danger_accept_invalid_certs=False                (default),
)
Listening for new data notifications ...
Stop with Ctrl+C.
```

Each line is a setting, its value and where it came from. `auth="bearer"` from
the credentials file means the DESP token was found; the token itself is never
printed, so the block is safe to paste into a support request.

Matching notifications are then printed as they arrive. Stop with `Ctrl + C`.

> [!IMPORTANT]
> `aviso-extremes-dt.py` receives only notifications published **after** it
> starts. Silence is normal until new data arrives. To see past notifications,
> run one of the scripts that start from a past time, such as
> `aviso-extremes-dt-from-time.py`. Section 7 explains the start positions.

---

## 6. Core Concepts

### 6.1 Client

A client holds the connection: the server address and the credential.

```python
import pyaviso

client = pyaviso.AvisoClient(
    base_url="https://aviso2.lumi.apps.dte.destination-earth.eu"
)
```

The credential is found automatically, in this order: the `AVISO_TOKEN`
environment variable (or `AVISO_USERNAME` with `AVISO_PASSWORD`), an `auth:`
block in `~/.config/aviso/config.yaml`, then `~/.config/aviso/credentials.yaml`. `print(client.config)` shows which one was
used.

`pyaviso.AsyncAvisoClient` is the same client for `asyncio` code.

### 6.2 Event Type

For DestinE Digital Twin data, the event type is always `"data"`:

```python
with client.listen("data", filter={...}) as notifications:
    ...
```

It is the only event type this server offers.

### 6.3 Filter Keys (MARS-like)

The filter uses keys from the MARS language. A notification is delivered only
when **every** key in the filter matches. The fewer keys you include, the
broader the subscription.

| Key       | Typical value         | Meaning                                  | Several values with `{"in": [...]}` |
| --------- | --------------------- | ---------------------------------------- | ----------------------------------- |
| `class`   | `"d1"`                | Destination Earth class                  | no                                  |
| `expver`  | `"0001"`              | Experiment version (operational)         | no                                  |
| `stream`  | `"oper"`, `"wave"`    | Data stream                              | yes                                 |
| `type`    | `"fc"`                | Forecast                                 | no                                  |
| `levtype` | `"sfc"`, `"pl"`, `"hl"` | Level type                             | yes                                 |
| `domain`  | `"g"`                 | Global                                   | yes                                 |
| `date`    | `"YYYYMMDD"`          | Forecast base date                       | no                                  |
| `time`    | `"0000"`              | Forecast base time                       | no                                  |
| `step`    | `6`                   | Forecast lead time in hours              | yes, and ranges                     |

A single value matches exactly. Where pyaviso 1 took a list, pyaviso 2 takes an
`in` constraint:

```python
filter = {
    "class": "d1",
    "expver": "0001",
    "stream": "oper",
    "levtype": "sfc",
    "type": "fc",
    "step": {"in": [0, 3, 6, 9, 12]},  # any of these steps
}
```

`step` also accepts ranges: `{"gte": 24}`, `{"lt": 6}` or `{"between": [0, 24]}`
(inclusive). A key the server does not know is rejected rather than ignored,
so a typo fails loudly. The server's own list is at the
[schema endpoint](#4-service-endpoints-and-connectivity).

> [!NOTE]
> Polytope request dictionaries accept additional keys (e.g., `"param"`,
> `"feature"`, `"dataset"`) and follow different validation rules since they
> are processed by separate software. Refer to the
> [Polytope documentation](https://platform.destine.eu/docs/climate-dt-user-guide/doc/data/polytope.html)
> and the [polytope-examples](https://github.com/destination-earth-digital-twins/polytope-examples)
> repository for building valid Polytope requests.

### 6.4 The Notification Object

Each notification from `listen()` is an object:

| Attribute          | Example                                              |
| ------------------ | ---------------------------------------------------- |
| `identifier`       | `{"class": "d1", "date": "20260921", "time": "0000", "step": "6", ...}` |
| `payload`          | extra data from the producer, or `None`              |
| `sequence`         | `8935`, its position on the server                   |
| `cloudevent`       | the full CloudEvent; `cloudevent["time"]` is when it was published |

All `identifier` values are **strings**, including `step`. Use them directly
in a Polytope request, or convert with `int(n.identifier["step"])` for
arithmetic. `print(notification)` prints the whole CloudEvent as JSON.

### 6.5 Processing: the Loop and Triggers

In pyaviso 2 your code is a plain loop:

```python
with client.listen("data", filter=FILTER) as notifications:
    for notification in notifications:
        download(notification.identifier)
```

`Trigger.function` calls a Python function for each notification instead,
and `run()` replaces the loop:

```python
from pyaviso import Trigger

client.listen("data", filter=FILTER, triggers=[Trigger.function(download)]).run()
```

Built-in **triggers** run an action for every notification before it reaches
the loop, with no code of your own:

| Trigger                     | Use case                                                    |
| --------------------------- | ----------------------------------------------------------- |
| `Trigger.echo()`            | Print to stdout: simplest, good for testing.                |
| `Trigger.log(path)`         | Append each notification to a JSON-lines file.              |
| `Trigger.command(cmd)`      | Run a shell command for each notification.                  |
| `Trigger.post(url)`         | Forward the [CloudEvent](https://cloudevents.io/) over HTTP. |
| `Trigger.webhook(url, ...)` | Send an HTTP request with a body you choose.                |
| `Trigger.teams(url)`        | Post a card to a Microsoft Teams workflow webhook.          |

```python
from pyaviso import Trigger

with client.listen(
    "data", filter=FILTER, triggers=[Trigger.log("aviso.jsonl")]
) as notifications:
    for notification in notifications:
        ...
```

### 6.6 Several Listeners

`listen_many()` opens several listeners, each with its own filter and
triggers, and processes their notifications in one loop. Each item is the
listener name and the notification:

```python
listeners = {
    "surface": {"event_type": "data", "filter": SURFACE_FILTER},
    "wave": {"event_type": "data", "filter": WAVE_FILTER},
}
with client.listen_many(listeners) as notifications:
    for name, notification in notifications:
        ...
```

`aviso-extremes-dt-multi-listener.py` gives each listener a trigger and calls
`run()` instead of writing the loop.

---

## 7. Catch-up, Replay and Resume

By default `listen()` delivers only notifications published after it starts.
Two arguments change that:

```python
# Replay everything published since 1 September 2026, then continue live
client.listen("data", filter=FILTER, start_from="2026-09-01T00:00:00Z")

# Replay that history, then stop instead of continuing live
client.listen(
    "data", filter=FILTER, start_from="2026-09-01T00:00:00Z", mode="replay_only"
)
```

`start_from` takes a **UTC string**. (An integer means a sequence number, not a
date: `start_from=20260901` starts after sequence 20,260,901.) There is no
`to_date`: to stop at a given time, use `mode="replay_only"` and leave the loop
at the first notification published after it, as
`aviso-extremes-dt-replay-window.py` does.

### 7.1 Start Positions are Publication Times, Not Forecast Base Times

> [!WARNING]
> `start_from` refers to the **wall-clock time when the notification was
> published** on the Aviso server, i.e. when the producer announced that a
> product was available. It is **not** the forecast base time (`date` + `time`
> in the filter).
>
> **Example scenario:**
> Data for the forecast initialised at `2025-11-04 00 UTC` typically becomes
> available around 8:00–11:00 UTC that same day. However, due to queuing delays
> or system issues, the corresponding notifications may be published several
> hours or even days later.
>
> **Correct approach:**
>
> - To replay all notifications for the `2025-11-04 00 UTC` cycle, set
>   `start_from` to a time *before* the cycle started (e.g.
>   `"2025-11-03T12:00:00Z"`) and put `"date": "20251104", "time": "0000"` in
>   the **filter**.
> - If you set `start_from="2025-11-04T12:00:00Z"`, you will only capture
>   notifications *published* from noon UTC onward, which may miss early steps
>   and include products from prior forecast cycles.
> - When in doubt, start conservatively early and rely on the filter to select
>   the correct forecasts.

### 7.2 The Replay Limit

The server replays at most **10,000 notifications per request**. A replay that
would exceed it stops with `pyaviso.HistoryGapError: history gap:
replay_limit_reached` rather than silently returning a partial history. If you
see it, narrow the filter (`stream`, `levtype`, `step`) or start later. The
examples catch this error and say so.

### 7.3 Resuming After a Restart

pyaviso 1 remembered the last notification it received and caught up
automatically on the next start. pyaviso 2 does this when you give the client
a **state store**:

```python
client = pyaviso.AvisoClient(
    base_url=AVISO_URL,
    state_store=pyaviso.JsonFileStore("~/.config/aviso/extremes-dt-state.json"),
)
with client.listen("data", filter=FILTER) as notifications:  # no start_from
    ...
```

The next run with the same server, event type and filter continues after the
saved position. An explicit `start_from` overrides it. Changing the filter
starts a new position. The last notification before a stop may be delivered
again, so make processing safe to repeat. `aviso-extremes-dt-resume.py` shows
the full pattern, including where the first run starts.

> [!NOTE]
> The saved position records what the client **received**, not what your code
> **finished**. With a state store the client reads at most one notification
> ahead of your loop, so a crash during long processing (a large download, say)
> can skip that one. If every notification must be processed, record completed
> work yourself.

---

## 8. Scope: Extremes Digital Twin Only

Notifications available through this server are limited to the **Extremes
Digital Twin**:

- `class: d1`, `expver: 0001`
- `stream: oper` (and `wave` for the wave component)
- 4 km global resolution; operational production began on **2023-12-11**

Climate DT data is not available through Aviso at this time.

Consult the [Extremes DT Data Catalogue](https://confluence.ecmwf.int/display/DDCZ/Extremes+DT+data+catalogue)
to identify available variables, levels, and forecast steps before constructing
your filter.

---

## 9. Examples in this Folder

| Script | Description |
| --- | --- |
| [`aviso-extremes-dt.py`](aviso-extremes-dt.py) | Minimal real-time listener that prints each notification. |
| [`aviso-extremes-dt-from-time.py`](aviso-extremes-dt-from-time.py) | Replay from a given publish time, then continue listening live. |
| [`aviso-extremes-dt-replay-window.py`](aviso-extremes-dt-replay-window.py) | Replay a bounded historical window and exit. |
| [`aviso-extremes-dt-resume.py`](aviso-extremes-dt-resume.py) | Save the position and resume after a restart (new in v2). |
| [`aviso-extremes-dt-log.py`](aviso-extremes-dt-log.py) | Persist every notification to a JSON-lines file with `Trigger.log`. |
| [`aviso-extremes-dt-multi-listener.py`](aviso-extremes-dt-multi-listener.py) | Two listeners with different filters in one loop (surface and wave). |
| [`aviso-extremes-dt-polytope-download.py`](aviso-extremes-dt-polytope-download.py) | Download a 2 m temperature time series from Polytope for every matching step. |
| [`aviso-extremes-dt-earthkit-example.py`](aviso-extremes-dt-earthkit-example.py) | End-to-end workflow: notification → Polytope download → regrid → Europe map plot. |

Every script except `aviso-extremes-dt-resume.py` has a pyaviso 1 counterpart
of the same name in [`../v1/`](../v1/).

---

## 10. Best Practices

- Use the **narrowest filter** possible (`stream`, `levtype`, `step`): it keeps
  replays under the [replay limit](#72-the-replay-limit) and avoids processing
  irrelevant notifications.
- The client keeps receiving while your loop works, so a slow step (a
  download, a plot) does not lose notifications: a few wait in a buffer, and
  beyond that the client reads more slowly from the server rather than
  dropping any. For sustained heavy processing, hand work to a queue or worker
  pool (e.g. `concurrent.futures`), or forward notifications with
  `Trigger.post`.
- Catch errors **per notification** in the loop, as the Polytope examples do,
  so that one failed download does not stop the listener.
- Each notification typically corresponds to one forecast step, so download
  volume scales directly with how broad your filter is.

---

## 11. Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| `401 Unauthorized` / `Authentication is required for this stream` | No DESP credential was found. Run `python desp-authentication.py` in the repository root, then check that `print(client.config)` shows `auth="bearer"` from the credentials file. |
| `client.config` shows `auth` from the environment or `config.yaml` rather than the credentials file | Those sources take precedence. Unset `AVISO_TOKEN` (and `AVISO_USERNAME`/`AVISO_PASSWORD`), or remove the `auth:` block from `~/.config/aviso/config.yaml`, to use the DESP token. |
| `401` after working for a long time | The DESP token expired. Re-run `desp-authentication.py`; a running listener picks up the new token. |
| The script prints `Listening ...` and no notifications arrive | Nothing matching has been published since it started, or the filter is too narrow. Try `aviso-extremes-dt-from-time.py`. |
| `HistoryGapError: history gap: replay_limit_reached` | More than 10,000 notifications match the replay; narrow the filter or start later. See [§7.2](#72-the-replay-limit). |
| `400` naming an unknown identifier | A filter key is misspelt or not in the [schema](#4-service-endpoints-and-connectivity). |
| Polytope error `Date is too old, expected > YYYYMMDD` | Polytope keeps only recent data online; the notification refers to a forecast outside that window. |
| Replay returns fewer events than expected | `start_from` is a publish time, not a forecast base time. See [§7.1](#71-start-positions-are-publication-times-not-forecast-base-times). |
| The script hangs after printing the configuration, or raises `TransportError` | The client cannot reach the server and keeps retrying. Check with `curl https://aviso2.lumi.apps.dte.destination-earth.eu/api/v1/schema`; outbound port 443 may be blocked by your network. |

---

## 12. References

- pyaviso 2 documentation: <https://sites.ecmwf.int/docs/aviso-client/stable/>
  - Python guide: <https://sites.ecmwf.int/docs/aviso-client/stable/python/overview.html>
  - Filters and start positions: <https://sites.ecmwf.int/docs/aviso-client/stable/python/listen.html>
  - Triggers: <https://sites.ecmwf.int/docs/aviso-client/stable/python/triggers.html>
  - State and resume: <https://sites.ecmwf.int/docs/aviso-client/stable/python/state-and-resume.html>
- pyaviso on PyPI: <https://pypi.org/project/pyaviso/>
- Destination Earth user guide: <https://platform.destine.eu/services/documents-and-api/doc/?service_name=climate-dt-user-guide>
- Polytope examples repository: <https://github.com/destination-earth-digital-twins/polytope-examples>
- Destination Earth: <https://destination-earth.eu/>
- DestinE / ECMWF Digital Twin Engine: <https://destine.ecmwf.int/>
- Extremes DT Data Catalogue: <https://confluence.ecmwf.int/display/DDCZ/Extremes+DT+data+catalogue>
- Earthkit: <https://earthkit.readthedocs.io/>
- CloudEvents specification: <https://cloudevents.io/>
