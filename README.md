# Aviso Examples for DT Data Availability Notifications <!-- omit from toc -->

This repository demonstrates how to access **Destination Earth (DestinE)
Digital Twin (DT)** data availability notifications using the Aviso
service hosted on the LUMI Databridge.

It provides simple example scripts to:

-   Listen for new DT data notifications
-   Replay historical notifications
-   Trigger automated workflows when new data becomes available

------------------------------------------------------------------------
# Table of Contents <!-- omit from toc -->

- [1. Overview](#1-overview)
- [2. Getting Started](#2-getting-started)
  - [2.1 Prerequisites](#21-prerequisites)
  - [2.2 Installation](#22-installation)
- [3. Running the Examples](#3-running-the-examples)
  - [3.1 Real-Time Listener Example](#31-real-time-listener-example)
    - [Expected Output](#expected-output)
- [4. Description of Example Scripts](#4-description-of-example-scripts)
  - [4.1 `aviso-extremes-dt.py`](#41-aviso-extremes-dtpy)
  - [4.2 `aviso-extremes-dt-from-time.py`](#42-aviso-extremes-dt-from-timepy)
  - [4.3 `aviso-extremes-dt-earthkit-example.py`](#43-aviso-extremes-dt-earthkit-examplepy)
- [5. Aviso Quota Limits for DestinE](#5-aviso-quota-limits-for-destine)

------------------------------------------------------------------------

# 1. Overview

The examples use the `pyaviso` client to subscribe to notification
topics exposed by Destination Earth and LUMI.

The scripts demonstrate:
-   Real-time notification listening
-   Recovery of missed notifications
-   Replay of historical notifications
-   Integration with the Earthkit ecosystem for automated workflows

------------------------------------------------------------------------

# 2. Getting Started

## 2.1 Prerequisites

-   Python >= **3.6** 
-   Outbound HTTPS connectivity to:
**aviso.lumi.apps.dte.destination-earth.eu (TCP port 443)**

If operating within a corporate or institutional network, ensure that firewall, proxy, and network security policies permit outbound access to this endpoint.

This can be checked with:
``` bash
curl -v https://aviso.lumi.apps.dte.destination-earth.eu
```

Authentication is currently **not required**.
Support for Destination Earth credentials will be added in the future.

------------------------------------------------------------------------

## 2.2 Installation

Install the Aviso Python client from PyPI:

``` bash
pip install pyaviso
```

If running the Earthkit integration example, install additional dependencies:

``` bash
pip install earthkit
```

------------------------------------------------------------------------

# 3. Running the Examples

All scripts can be executed directly with Python.

## 3.1 Real-Time Listener Example

Run:

``` bash
python3 aviso-extremes-dt.py
```

### Expected Output

As output you should expect something like:

``` bash
loaded config:
{'auth_type': 'none',
  'configuration_engine': {'host': 'aviso.lumi.apps.dte.destination-earth.eu',
                          'https': True,
                          'port': 443},
  'notification_engine': {'host': 'aviso.lumi.apps.dte.destination-earth.eu',
                          'https': True,
                          'port': 443},
  'remote_schema': True,
  'schema_parser': 'generic'
  }
Listening to /de/data/ at aviso.lumi.apps.dte.destination-earth.eu:443...
```

Upon execution, the client loads its configuration and subscribes to the specified notification topic. Notifications will be printed to standard output as they are received.

Terminate execution using:

``` bash
Ctrl + C
```
------------------------------------------------------------------------


# 4. Description of Example Scripts

## 4.1 `aviso-extremes-dt.py`

This script:

1.  Defines a **request dictionary** describing the notification topic.
2.  Connects to the Aviso notification engine.
3.  Executes an **echo trigger** for each notification (prints to
    screen).
4.  Continues polling until interrupted.


> ⚠️ **IMPORTANT NOTE:**  
>Before listening to new notifications, Aviso:
>-   Checks the last received notification.
>-   Retrieves any missed notifications.
>-   Then switches to real-time listening.
>
>On first execution, no previous notifications are returned.
>
>This ensures users do not miss notifications after machine reboots or
>interruptions.

------------------------------------------------------------------------

## 4.2 `aviso-extremes-dt-from-time.py`

This script demonstrates:

-   Searching for **historical** notifications from a specified time.
-   Executing a trigger function for each retrieved notification.
-   Continuing with live listening afterward.

The trigger function in this example simply prints notifications, but it
can be replaced with custom processing logic.

------------------------------------------------------------------------

## 4.3 `aviso-extremes-dt-earthkit-example.py`

This example demonstrates a complete automated workflow:

1.  Listen for new Extremes DT data notifications.
2.  Trigger a function when a notification is received.
3.  Retrieve temperature data via Polytope.
4.  Regrid to a coarser resolution (for faster processing)
5.  Generate a plot of the data bounded by Europe using Earthkit plots library.

It shows how Aviso can act as an event-driven entry point for data
processing pipelines.

------------------------------------------------------------------------

# 5. Aviso Quota Limits for DestinE

To ensure system stability and fair usage, the following limits apply:

-   **Rate Limit:** Up to **50 requests per second** (may be adjusted
    depending on system load)
-   **Concurrent Operations:** Currently not limited

Please design your workflows accordingly to avoid service interruptions.

------------------------------------------------------------------------