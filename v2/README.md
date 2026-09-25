# Aviso for Destination Earth: Extremes Digital Twin (pyaviso 2) <!-- omit from toc -->

These examples use **pyaviso 2** and the Aviso server at
`https://aviso2.lumi.apps.dte.destination-earth.eu`. They replace the pyaviso 1
examples in [`../v1/`](../v1/). pyaviso 1 and its server will be
decommissioned at the beginning of 2027. The
[repository README](../README.md) compares the two versions.

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

[Aviso](https://sites.ecmwf.int/docs/aviso-client/main/) is a notification
system developed by **ECMWF**. It announces time-critical events, such as the
availability of a new forecast step, so that workflows can react to them
without polling. For Destination Earth, Aviso announces new Digital Twin data
as soon as it is available. Post-processing, visualisation, model coupling or
alerting can then start without delay.

pyaviso 2 is a new client for a new server. It is not a drop-in replacement
for pyaviso 1: listeners, filters and start positions are expressed
differently.
Section 4 of the [repository README](../README.md#4-migrating-from-v1-to-v2)
lists the pyaviso 2 equivalent of each pyaviso 1 construct.

---

## 2. Installation

pyaviso 2 requires Python 3.10 or newer. pyaviso 1 and pyaviso 2 are published
under the same package name, so pyaviso 2 must be installed in a dedicated
virtual environment:

```bash
python3 -m venv .venv-v2
source .venv-v2/bin/activate
pip install -r requirements.txt
```

A minimal installation, for listening only, without data download or
plotting:

```bash
pip install "pyaviso>=2.2.2,<3" conflator lxml requests
```

`conflator`, `lxml` and `requests` are required by `desp-authentication.py`.

---

## 3. Requirements and Access

> [!IMPORTANT]
> Unlike pyaviso 1, pyaviso 2 requires a **DESP credential to listen**.
> Without one, the server responds with `401 Unauthorized`. Downloading data
> through Polytope requires the same credential.

To obtain DESP credentials:

1. Register at the [DestinE Platform](https://platform.destine.eu/).
2. Apply for upgraded access as described in the
   [access policy](https://platform.destine.eu/support-pages/access-policy/).

Once upgraded access has been granted, run
[`desp-authentication.py`](../desp-authentication.py) from the repository root.
The script writes the DESP offline token to `~/.polytopeapirc` for Polytope
and to `~/.config/aviso/credentials.yaml` for pyaviso 2. The examples read the
credential from that file, so it does not appear in the code. The options of
the script are described in
[Access and Authentication](../README.md#2-access-and-authentication).

---

## 4. Service Endpoints and Connectivity

| Setting              | Value                                               |
| -------------------- | --------------------------------------------------- |
| Aviso server         | `https://aviso2.lumi.apps.dte.destination-earth.eu` |
| Port                 | `443` (HTTPS)                                       |
| Polytope host (data) | `polytope.lumi.apps.dte.destination-earth.eu`       |

The schema endpoint of the server does not require a credential. It can be
used to test connectivity and to list the filter keys that the server accepts:

```bash
curl https://aviso2.lumi.apps.dte.destination-earth.eu/api/v1/schema
```

On a corporate or institutional network, the firewall or proxy must allow
outbound TCP connections to the Aviso host on port 443.

---

## 5. Running the Examples

Run all scripts from this folder (`v2/`):

```bash
python aviso-extremes-dt.py
```

Each script first prints the connection settings it uses:

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

Each line shows a setting, its value and the source of the value.
`auth="bearer"` with the credentials file as its source confirms that the DESP
token was found. The token itself is never printed, so this output can be
included in a support request.

The script then prints matching notifications as they arrive. Press `Ctrl+C`
to stop it.

> [!IMPORTANT]
> `aviso-extremes-dt.py` receives only notifications published **after** it
> starts, so it prints nothing until new data is published. To see past
> notifications, run a script that starts from a past time, such as
> `aviso-extremes-dt-from-time.py`. Start positions are described in
> section 7.

---

## 6. Core Concepts

### 6.1 Client

A client holds the server address and the credential.

```python
import pyaviso

client = pyaviso.AvisoClient(
    base_url="https://aviso2.lumi.apps.dte.destination-earth.eu"
)
```

The client finds the credential automatically. It checks the following
sources in order:

1. the `AVISO_TOKEN` environment variable, or `AVISO_USERNAME` with
   `AVISO_PASSWORD`;
2. an `auth:` block in `~/.config/aviso/config.yaml`;
3. `~/.config/aviso/credentials.yaml`.

`print(client.config)` shows which source was used.

`pyaviso.AsyncAvisoClient` provides the same interface for `asyncio` code.

### 6.2 Event Type

For DestinE Digital Twin data, the event type is always `"data"`:

```python
with client.listen("data", filter={...}) as notifications:
    ...
```

It is the only event type that this server provides.

### 6.3 Filter Keys (MARS-like)

The filter uses keys from the MARS language. A notification is delivered only
when **every** key in the filter matches. A filter with fewer keys matches more
notifications.

| Key       | Typical value           | Meaning                          | Several values with `{"in": [...]}` |
| --------- | ----------------------- | -------------------------------- | ----------------------------------- |
| `class`   | `"d1"`                  | Destination Earth class          | no                                  |
| `expver`  | `"0001"`                | Experiment version (operational) | no                                  |
| `stream`  | `"oper"`, `"wave"`      | Data stream                      | yes                                 |
| `type`    | `"fc"`                  | Forecast                         | no                                  |
| `levtype` | `"sfc"`, `"pl"`, `"hl"` | Level type                       | yes                                 |
| `domain`  | `"g"`                   | Global                           | yes                                 |
| `date`    | `"YYYYMMDD"`            | Forecast base date               | no                                  |
| `time`    | `"0000"`                | Forecast base time               | no                                  |
| `step`    | `6`                     | Forecast lead time in hours      | yes, and ranges                     |

A single value matches exactly. Where pyaviso 1 accepted a list of values,
pyaviso 2 accepts an `in` constraint:

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

`step` also accepts ranges: `{"gte": 24}`, `{"lt": 6}` or
`{"between": [0, 24]}` (inclusive). The server rejects a key that it does not
recognise, so a misspelt key causes an error instead of being ignored. The
[schema endpoint](#4-service-endpoints-and-connectivity) lists the accepted
keys.

> [!NOTE]
> Polytope request dictionaries accept additional keys (for example
> `"param"`, `"feature"` and `"dataset"`) and follow different validation
> rules, because they are processed by separate software. Refer to the
> [Polytope documentation](https://platform.destine.eu/docs/climate-dt-user-guide/doc/data/polytope.html)
> and the [polytope-examples](https://github.com/destination-earth-digital-twins/polytope-examples)
> repository to build valid Polytope requests.

### 6.4 The Notification Object

`listen()` delivers each notification as an object with the following
attributes:

| Attribute    | Example                                                                 |
| ------------ | ----------------------------------------------------------------------- |
| `identifier` | `{"class": "d1", "date": "20260921", "time": "0000", "step": "6", ...}` |
| `payload`    | additional data from the producer, or `None`                            |
| `sequence`   | `8935`, the position of the notification on the server                  |
| `cloudevent` | the complete CloudEvent; `cloudevent["time"]` is the publication time   |

All `identifier` values are **strings**, including `step`. They can be used
directly in a Polytope request. For arithmetic, convert them first, for
example with `int(notification.identifier["step"])`. `print(notification)`
prints the complete CloudEvent as JSON.

### 6.5 Processing: the Loop and Triggers

In pyaviso 2, notifications are processed in a loop:

```python
with client.listen("data", filter=FILTER) as notifications:
    for notification in notifications:
        download(notification.identifier)
```

Alternatively, `Trigger.function` calls a Python function for each
notification, and `run()` replaces the loop:

```python
from pyaviso import Trigger

client.listen("data", filter=FILTER, triggers=[Trigger.function(download)]).run()
```

Built-in **triggers** perform an action for each notification before the loop
receives it, without additional code:

| Trigger                     | Action                                                         |
| --------------------------- | -------------------------------------------------------------- |
| `Trigger.echo()`            | Print the notification to standard output. Useful for testing. |
| `Trigger.log(path)`         | Append the notification to a JSON Lines file.                  |
| `Trigger.command(cmd)`      | Run a shell command.                                           |
| `Trigger.post(url)`         | Forward the [CloudEvent](https://cloudevents.io/) over HTTP.   |
| `Trigger.webhook(url, ...)` | Send an HTTP request with a configurable body.                 |
| `Trigger.teams(url)`        | Post a card to a Microsoft Teams workflow webhook.             |

```python
with client.listen(
    "data", filter=FILTER, triggers=[Trigger.log("aviso.jsonl")]
) as notifications:
    for notification in notifications:
        ...
```

### 6.6 Several Listeners

`listen_many()` opens several listeners, each with its own filter and
triggers, and processes their notifications in one loop. Each item is a pair
of the listener name and the notification:

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
`run()` in place of the loop.

---

## 7. Catch-up, Replay and Resume

By default, `listen()` delivers only notifications published after it starts.
Two arguments change this behaviour:

```python
# Replay all notifications published since 1 September 2026, then continue
# with new notifications
client.listen("data", filter=FILTER, start_from="2026-09-01T00:00:00Z")

# Replay the same history, then stop
client.listen(
    "data", filter=FILTER, start_from="2026-09-01T00:00:00Z", mode="replay_only"
)
```

`start_from` takes a **UTC time string**. An integer is interpreted as a
sequence number, not as a date: `start_from=20260901` starts after sequence
number 20,260,901. There is no `to_date` argument. To stop at a given time,
use `mode="replay_only"` and leave the loop at the first notification
published after that time, as `aviso-extremes-dt-replay-window.py` does.

### 7.1 Start Positions are Publication Times, Not Forecast Base Times

> [!WARNING]
> `start_from` refers to the **time at which a notification was published**
> on the Aviso server, that is, when the producer announced that a product was
> available. It does **not** refer to the forecast base time (`date` and
> `time` in the filter).
>
> **Example:**
> Data for the forecast initialised at `2025-11-04 00 UTC` usually becomes
> available between 08:00 and 11:00 UTC on the same day. Queuing delays or
> operational problems can, however, delay the corresponding notifications by
> several hours or days.
>
> **Recommended approach:**
>
> - To replay all notifications for the `2025-11-04 00 UTC` cycle, set
>   `start_from` to a time *before* the cycle started (for example
>   `"2025-11-03T12:00:00Z"`), and select the cycle in the **filter** with
>   `"date": "20251104", "time": "0000"`.
> - With `start_from="2025-11-04T12:00:00Z"`, only notifications *published*
>   from 12:00 UTC onwards are replayed. The replay may therefore miss early
>   steps and include products from earlier forecast cycles.
> - If in doubt, choose an earlier start time and let the filter select the
>   forecasts.

### 7.2 The Replay Limit

The server replays at most **10,000 notifications per request**. A replay that
would exceed this limit stops with
`pyaviso.HistoryGapError: history gap: replay_limit_reached`, so an incomplete
history is never returned without an error. In that case, narrow the filter
(`stream`, `levtype`, `step`) or choose a later start time. The examples
handle this error and print an explanatory message.

### 7.3 Resuming After a Restart

pyaviso 1 recorded the last notification it received and, on the next start,
automatically delivered the notifications published in the meantime.
pyaviso 2 does the same when the client is given a **state store**:

```python
client = pyaviso.AvisoClient(
    base_url=AVISO_URL,
    state_store=pyaviso.JsonFileStore("~/.config/aviso/extremes-dt-state.json"),
)
with client.listen("data", filter=FILTER) as notifications:  # no start_from
    ...
```

The next run with the same server, event type and filter continues after the
saved position. An explicit `start_from` takes precedence over the saved
position, and a different filter starts from a new position. The last
notification received before a stop may be delivered again, so processing
should be safe to repeat. `aviso-extremes-dt-resume.py` shows the complete
pattern, including the start position of the first run.

> [!NOTE]
> The saved position records which notifications the client has
> **received**, not which ones the application has **processed**. With a
> state store, the client reads at most one notification ahead of the loop.
> If the process stops during lengthy processing, such as a large download,
> that notification may therefore be skipped on the next run. If every
> notification must be processed, record completed work in the application.

---

## 8. Scope: Extremes Digital Twin Only

This server provides notifications for the **Extremes Digital Twin** only:

- `class: d1`, `expver: 0001`
- `stream: oper`, and `wave` for the wave component
- 4 km global resolution; operational production began on **2023-12-11**

Climate DT data is currently not available through Aviso.

The [Extremes DT Data Catalogue](https://confluence.ecmwf.int/display/DDCZ/Extremes+DT+data+catalogue)
lists the available variables, levels and forecast steps. Consult it before
defining a filter.

---

## 9. Examples in this Folder

| Script | Description |
| --- | --- |
| [`aviso-extremes-dt.py`](aviso-extremes-dt.py) | Minimal listener that prints each new notification. |
| [`aviso-extremes-dt-from-time.py`](aviso-extremes-dt-from-time.py) | Replay from a given publication time, then continue with new notifications. |
| [`aviso-extremes-dt-replay-window.py`](aviso-extremes-dt-replay-window.py) | Replay a bounded time window, then exit. |
| [`aviso-extremes-dt-resume.py`](aviso-extremes-dt-resume.py) | Save the position and resume after a restart (new in v2). |
| [`aviso-extremes-dt-log.py`](aviso-extremes-dt-log.py) | Write every notification to a JSON Lines file with `Trigger.log`. |
| [`aviso-extremes-dt-multi-listener.py`](aviso-extremes-dt-multi-listener.py) | Two listeners with different filters in one loop (surface and wave). |
| [`aviso-extremes-dt-polytope-download.py`](aviso-extremes-dt-polytope-download.py) | Download a 2 m temperature time series from Polytope for each matching step. |
| [`aviso-extremes-dt-earthkit-example.py`](aviso-extremes-dt-earthkit-example.py) | Complete workflow: notification, Polytope download, regridding and a map of Europe. |

Each script except `aviso-extremes-dt-resume.py` has a pyaviso 1 counterpart
with the same name in [`../v1/`](../v1/).

---

## 10. Best Practices

- Use the **narrowest possible filter** (`stream`, `levtype`, `step`). This
  keeps replays under the [replay limit](#72-the-replay-limit) and avoids
  processing notifications that are not needed.
- The client continues to receive notifications while the loop is busy, so a
  slow step, such as a download or a plot, does not cause notifications to be
  lost. A small number are buffered; beyond that, the client reads from the
  server more slowly instead of discarding notifications. For sustained heavy
  processing, pass the work to a queue or a worker pool (for example
  `concurrent.futures`), or forward notifications with `Trigger.post`.
- Handle errors **for each notification** inside the loop, as the Polytope
  examples do, so that a single failed download does not stop the listener.
- Each notification usually corresponds to one forecast step, so the download
  volume grows with the breadth of the filter.

---

## 11. Troubleshooting

| Symptom | Cause and solution |
| --- | --- |
| `401 Unauthorized` or `Authentication is required for this stream` | No DESP credential was found. Run `python desp-authentication.py` in the repository root, then check that `print(client.config)` shows `auth="bearer"` from the credentials file. |
| `client.config` shows `auth` from the environment or `config.yaml` instead of the credentials file | These sources take precedence. To use the DESP token, unset `AVISO_TOKEN` (and `AVISO_USERNAME` and `AVISO_PASSWORD`), or remove the `auth:` block from `~/.config/aviso/config.yaml`. |
| `401` after a long period of successful operation | The DESP token has expired. Run `desp-authentication.py` again; a running listener then uses the new token. |
| The script prints `Listening ...` but no notifications arrive | No matching notification has been published since the script started, or the filter is too narrow. Run `aviso-extremes-dt-from-time.py` to see past notifications. |
| `HistoryGapError: history gap: replay_limit_reached` | More than 10,000 notifications match the replay. Narrow the filter or choose a later start time. See [section 7.2](#72-the-replay-limit). |
| `400` naming an unknown identifier | A filter key is misspelt or not defined in the [schema](#4-service-endpoints-and-connectivity). |
| Polytope error `Date is too old, expected > YYYYMMDD` | Polytope keeps only recent data online, and the notification refers to a forecast outside that period. |
| A replay returns fewer notifications than expected | `start_from` is a publication time, not a forecast base time. See [section 7.1](#71-start-positions-are-publication-times-not-forecast-base-times). |
| The script stops responding after printing the configuration, or raises `TransportError` | The client cannot reach the server and keeps retrying. Test the connection with `curl https://aviso2.lumi.apps.dte.destination-earth.eu/api/v1/schema`; the network may block outbound connections on port 443. |

---

## 12. References

- pyaviso 2 documentation: <https://sites.ecmwf.int/docs/aviso-client/main/>
  - Python guide: <https://sites.ecmwf.int/docs/aviso-client/main/python/overview.html>
  - Filters and start positions: <https://sites.ecmwf.int/docs/aviso-client/main/python/listen.html>
  - Triggers: <https://sites.ecmwf.int/docs/aviso-client/main/python/triggers.html>
  - Several listeners: <https://sites.ecmwf.int/docs/aviso-client/main/python/listen-many.html>
  - State and resume: <https://sites.ecmwf.int/docs/aviso-client/main/python/state-and-resume.html>
- pyaviso on PyPI: <https://pypi.org/project/pyaviso/>
- Destination Earth user guide: <https://platform.destine.eu/services/documents-and-api/doc/?service_name=climate-dt-user-guide>
- Polytope examples repository: <https://github.com/destination-earth-digital-twins/polytope-examples>
- Destination Earth: <https://destination-earth.eu/>
- DestinE / ECMWF Digital Twin Engine: <https://destine.ecmwf.int/>
- Extremes DT Data Catalogue: <https://confluence.ecmwf.int/display/DDCZ/Extremes+DT+data+catalogue>
- Earthkit: <https://earthkit.readthedocs.io/>
- CloudEvents specification: <https://cloudevents.io/>
