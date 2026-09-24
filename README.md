# Aviso for Destination Earth — Extremes Digital Twin <!-- omit from toc -->

This repository provides documentation and example scripts for using **Aviso**
to receive data-availability notifications for **Destination Earth (DestinE)
Digital Twin** data, with a focus on the **Extremes Digital Twin (Extremes-DT)**.

> [!CAUTION]
> **Two versions of Aviso are running, and the old one is going away.**
> pyaviso 1 and its server `aviso.lumi.apps.dte.destination-earth.eu` will be
> **decommissioned at the beginning of 2027**. Use pyaviso 2 and the
> [`v2/`](v2/) examples for anything new, and move existing workflows over
> before then.

## Table of Contents <!-- omit from toc -->

- [1. Which Version?](#1-which-version)
- [2. Access and Authentication](#2-access-and-authentication)
- [3. Quick Start](#3-quick-start)
- [4. Moving from v1 to v2](#4-moving-from-v1-to-v2)
- [5. Repository Layout](#5-repository-layout)

---

## 1. Which Version?

|                     | **v2** (use this)                                   | **v1** (deprecated)                          |
| ------------------- | --------------------------------------------------- | -------------------------------------------- |
| Python package      | `pyaviso>=2.2.1,<3`                                 | `pyaviso==1.0.2`                             |
| Server              | `https://aviso2.lumi.apps.dte.destination-earth.eu` | `aviso.lumi.apps.dte.destination-earth.eu`   |
| Listening needs     | a DESP credential                                   | nothing                                      |
| Python              | 3.10 or newer                                       | 3.6 or newer (listener only)                 |
| Examples and guide  | [`v2/`](v2/) and [`v2/README.md`](v2/README.md)     | [`v1/`](v1/) and [`v1/README.md`](v1/README.md) |
| Status              | supported                                           | decommissioned at the beginning of 2027      |

Each folder has the same examples under the same file names, so
`diff v1/<script> v2/<script>` shows exactly what changes when you migrate one.
The two servers keep separate histories: a v2 replay reaches back only to
when the v2 server started receiving Extremes-DT notifications.

> [!IMPORTANT]
> pyaviso 1 and pyaviso 2 are the **same package name** on PyPI, so they cannot
> be installed in the same Python environment. Give each version its own
> virtual environment, as in the [quick start](#3-quick-start).

---

## 2. Access and Authentication

To obtain DESP credentials:

1. Register at the [DestinE Platform](https://platform.destine.eu/).
2. Apply for upgraded access as described in the
   [access policy](https://platform.destine.eu/support-pages/access-policy/).

Once upgraded access is granted, run [`desp-authentication.py`](desp-authentication.py)
from the repository root:

```bash
python desp-authentication.py
```

It prompts for your DestinE username and password, retrieves a long-lived
offline token from the Destination Earth Service Platform (DESP), and writes it
to two places:

| File                                | Used by                                                      |
| ----------------------------------- | ------------------------------------------------------------ |
| `~/.polytopeapirc`                  | Polytope, for downloading data (both versions)               |
| `~/.config/aviso/credentials.yaml`  | pyaviso 2 and the `aviso` command, for listening             |

Re-run it when the token expires. A pyaviso 2 listener that is already running
and took its credential from `credentials.yaml` does not need a restart: when
the server rejects the old token, the client re-reads the file and retries
with the new one.

Options:

- `--aviso-outpath PATH` writes the Aviso credential elsewhere. pyaviso 2 then
  needs `AVISO_CREDENTIALS_FILE=PATH` to find it. If `AVISO_CREDENTIALS_FILE`
  is already set, the script writes there by default.
- `--aviso-outpath none` skips the Aviso credential.
- `-o PATH` / `-o stdout` controls the Polytope token, as before.

> [!NOTE]
> pyaviso 1 listens without authentication, so v1 users only need the token
> for Polytope downloads. pyaviso 2 needs it to listen at all: without it the
> server answers `401 Unauthorized`.

---

## 3. Quick Start

**v2**, from the repository root:

```bash
python3 -m venv .venv-v2
source .venv-v2/bin/activate
pip install -r v2/requirements.txt
python desp-authentication.py        # once; re-run when the token expires
cd v2
python aviso-extremes-dt-from-time.py
```

This replays the last two weeks of notifications and then keeps listening.
`aviso-extremes-dt.py` shows only new ones, so it can stay silent for a while.

The first thing each v2 script prints is the connection it resolved, for
example:

```text
ResolvedConfig(
    base_url='https://aviso2.lumi.apps.dte.destination-earth.eu/' (code),
    auth="bearer"                                    (credentials file /home/you/.config/aviso/credentials.yaml),
    ...
)
```

`auth="bearer"` from the credentials file means the DESP token was found. The
token itself is never printed.

**v1** (deprecated), in a separate environment:

```bash
python3 -m venv .venv-v1
source .venv-v1/bin/activate
pip install -r v1/requirements.txt
cd v1
python aviso-extremes-dt.py
```

---

## 4. Moving from v1 to v2

| pyaviso 1                                              | pyaviso 2                                                         |
| ------------------------------------------------------ | ----------------------------------------------------------------- |
| `NotificationManager()` plus a `CONFIG` dict           | `pyaviso.AvisoClient(base_url=AVISO_URL)`                         |
| `"auth_type": "none"`                                  | the DESP credential in `~/.config/aviso/credentials.yaml`         |
| a listener dict: `event`, `request`, `triggers`        | `client.listen("data", filter=..., triggers=...)`                 |
| `"request": {...}`                                     | `filter={...}`, with the same keys                                |
| a list of values: `"step": [0, 6, 12]`                 | `"step": {"in": [0, 6, 12]}`                                      |
| a `function` trigger                                   | a plain `for notification in ...:` loop                           |
| `notification["request"]["date"]`                      | `notification.identifier["date"]` (values are strings)            |
| `echo`, `log`, `command`, `post` triggers              | `Trigger.echo()`, `Trigger.log(path)`, `Trigger.command(...)`, `Trigger.post(url)` |
| `from_date=datetime(...)`                              | `start_from="2026-09-01T00:00:00Z"` (a UTC string)                |
| `to_date=datetime(...)`                                | `mode="replay_only"` and stop at the end time in the loop         |
| several listeners in one `listen()` call               | one `listen()` per filter; run them together with `AsyncAvisoClient` |
| catch-up after a restart, automatically                | `state_store=pyaviso.JsonFileStore(path)`                         |

Each row is shown in a script in [`v2/`](v2/); the [v2 guide](v2/README.md)
explains them in full.

---

## 5. Repository Layout

```text
desp-authentication.py   DESP login: writes the Polytope token and the Aviso credential
v2/                      pyaviso 2 examples and guide (use these)
v1/                      pyaviso 1 examples and guide (deprecated, removed in 2027)
```
