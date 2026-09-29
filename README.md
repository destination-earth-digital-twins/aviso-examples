# Aviso for Destination Earth: Extremes Digital Twin <!-- omit from toc -->

This repository contains documentation and example scripts for **Aviso**, the
service that sends notifications when **Destination Earth (DestinE) Digital
Twin** data becomes available. The examples cover the **Extremes Digital Twin
(Extremes-DT)**.

> [!CAUTION]
> **pyaviso 1 is deprecated.** The pyaviso 1 service will be
> **decommissioned at the beginning of 2027**. Its address,
> `aviso.lumi.apps.dte.destination-earth.eu`, will then serve the pyaviso 2
> server, and pyaviso 1 will no longer work with it. New workflows should use
> pyaviso 2 and the [`v2/`](v2/) examples. Existing workflows should be
> migrated before that date.

## Table of Contents <!-- omit from toc -->

- [1. Versions](#1-versions)
- [2. Access and Authentication](#2-access-and-authentication)
- [3. Quick Start](#3-quick-start)
- [4. Migrating from v1 to v2](#4-migrating-from-v1-to-v2)
- [5. Repository Layout](#5-repository-layout)

---

## 1. Versions

|                          | **v2** (recommended)                                | **v1** (deprecated)                             |
| ------------------------ | --------------------------------------------------- | ----------------------------------------------- |
| Python package           | `pyaviso>=2.4.0,<3`                                 | `pyaviso==1.0.2`                                |
| Server                   | `https://aviso2.lumi.apps.dte.destination-earth.eu` | `aviso.lumi.apps.dte.destination-earth.eu`      |
| Credential for listening | DESP credential required                            | none                                            |
| Python                   | 3.10 or newer                                       | 3.6 or newer (listener only)                    |
| Examples and guide       | [`v2/`](v2/) and [`v2/README.md`](v2/README.md)     | [`v1/`](v1/) and [`v1/README.md`](v1/README.md) |
| Status                   | supported                                           | decommissioned at the beginning of 2027         |

From the beginning of 2027, `aviso.lumi.apps.dte.destination-earth.eu` will
also serve the pyaviso 2 server, and either address can then be used with
pyaviso 2.

Both folders contain the same examples under the same file names. To see the
changes needed to migrate a script, compare the two versions with
`diff v1/<script> v2/<script>`.

The two servers keep separate histories. A replay on the v2 server can only
reach back to the date on which that server started to receive Extremes-DT
notifications.

> [!IMPORTANT]
> pyaviso 1 and pyaviso 2 are published under the **same package name** on
> PyPI, so they cannot be installed in the same Python environment. Use a
> separate virtual environment for each version, as shown in the
> [quick start](#3-quick-start).

---

## 2. Access and Authentication

To obtain DESP credentials:

1. Register at the [DestinE Platform](https://platform.destine.eu/).
2. Apply for upgraded access as described in the
   [access policy](https://platform.destine.eu/support-pages/access-policy/).

Once upgraded access has been granted, run
[`desp-authentication.py`](desp-authentication.py) from the repository root:

```bash
python desp-authentication.py
```

The script asks for your DestinE username and password and obtains a
long-lived offline token from the Destination Earth Service Platform (DESP).
It writes the token to two files:

| File                               | Used by                                      |
| ---------------------------------- | -------------------------------------------- |
| `~/.polytopeapirc`                 | Polytope, to download data (both versions)   |
| `~/.config/aviso/credentials.yaml` | pyaviso 2 and the `aviso` command, to listen |

Run the script again when the token expires. A running pyaviso 2 listener that
reads its credential from `credentials.yaml` does not need to be restarted.
When the server rejects the expired token, the client reads the file again and
retries with the new token.

The script accepts the following options:

- `--aviso-outpath PATH` writes the Aviso credential to `PATH`. pyaviso 2 then
  finds it only if `AVISO_CREDENTIALS_FILE` is set to `PATH`. If
  `AVISO_CREDENTIALS_FILE` is already set, the script writes to that location
  by default.
- `--aviso-outpath none` does not write the Aviso credential.
- `-o PATH` writes the Polytope token to `PATH`, and `-o stdout` prints it.

> [!NOTE]
> pyaviso 1 listens without authentication, so v1 users need the token only to
> download data with Polytope. pyaviso 2 requires the token to listen. Without
> it, the server responds with `401 Unauthorized`.

---

## 3. Quick Start

**v2**, from the repository root:

```bash
python3 -m venv .venv-v2
source .venv-v2/bin/activate
pip install -r v2/requirements.txt
python desp-authentication.py        # once; run again when the token expires
cd v2
python aviso-extremes-dt-from-time.py
```

This script replays the notifications of the last two weeks and then continues
to listen for new ones. `aviso-extremes-dt.py`, in contrast, shows only
notifications published after it starts, so it may print nothing for some
time.

Each v2 script first prints the connection settings it uses, for example:

```text
ResolvedConfig(
    base_url='https://aviso2.lumi.apps.dte.destination-earth.eu/' (code),
    auth="bearer"                                    (credentials file /home/you/.config/aviso/credentials.yaml),
    ...
)
```

`auth="bearer"` with the credentials file as its source confirms that the DESP
token was found. The token itself is never printed.

**v1** (deprecated), in a separate environment:

```bash
python3 -m venv .venv-v1
source .venv-v1/bin/activate
pip install -r v1/requirements.txt
cd v1
python aviso-extremes-dt.py
```

---

## 4. Migrating from v1 to v2

| pyaviso 1                                       | pyaviso 2                                                                          |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| `NotificationManager()` plus a `CONFIG` dict    | `pyaviso.AvisoClient(base_url=AVISO_URL)`                                          |
| `"auth_type": "none"`                           | the DESP credential in `~/.config/aviso/credentials.yaml`                          |
| a listener dict: `event`, `request`, `triggers` | `client.listen("data", filter=..., triggers=...)`                                  |
| `"request": {...}`                              | `filter={...}`, with the same keys                                                 |
| a list of values: `"step": [0, 6, 12]`          | `"step": {"in": [0, 6, 12]}`                                                       |
| a `function` trigger                            | `Trigger.function(f)`, or a plain `for notification in ...:` loop                  |
| `notification["request"]["date"]`               | `notification.identifier["date"]` (values are strings)                             |
| `echo`, `log`, `command`, `post` triggers       | `Trigger.echo()`, `Trigger.log(path)`, `Trigger.command(...)`, `Trigger.post(url)` |
| `from_date=datetime(...)`                       | `start_from="2026-09-01T00:00:00Z"` (a UTC string)                                 |
| `to_date=datetime(...)`                         | `mode="replay_only"`, and leave the loop at the end time                           |
| several listeners in one `listen()` call        | `client.listen_many({name: {...}, ...})`                                           |
| automatic catch-up after a restart              | `state_store=pyaviso.JsonFileStore(path)`                                          |

Each of these constructs is used in at least one script in [`v2/`](v2/). The
[v2 guide](v2/README.md) describes them in detail.

---

## 5. Repository Layout

```text
desp-authentication.py   DESP login: writes the Polytope token and the Aviso credential
v2/                      pyaviso 2 examples and guide (recommended)
v1/                      pyaviso 1 examples and guide (deprecated; the service ends in 2027)
```
