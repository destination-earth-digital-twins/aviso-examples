# Aviso Examples for DT Data Availability Notifications

This repository describes the process for accessing Destination Earth DT data  availability notifications via the Aviso service hosted on the LUMI Databridge.

## Getting Started

### Prerequisites
Before you begin, ensure you have Python installed on your system. **aviso** is compatible with Python 3.6+.

### Installation
To run the examples you simply need to install pyaviso package from PyPI:
```bash
pip  install  pyaviso
```

Authentication is not required to access notifications at this time; however, Destination Earth credentials will be supported in the future.

### Explanation

#### `aviso-extremes-dt.py`

This is an example script to listen for notifications described in the request dictionary at the beginning of the script. It executes an echo trigger per notification, which means printing a notification to the screen. After printing the notification, Aviso polls for new notifications until the user interrupts the script.

---
**IMPORTANT NOTE**
Before listening to new notifications, Aviso by default checks what the last notification was, and it will then return all the notifications that have been missed since. It will then carry on by listening to new ones. The first time the application runs, however, no previous notification will be returned. This behaviour allows users not to miss any notifications in the event of machine reboots.
---

#### `aviso-extremes-dt-from-time.py`

This example illustrates the functionality of searching for old notifications where available. This way users can explicitly replay past notifications and executes triggers. This particular example utilizes a function trigger per found notifications according to defined request dictionary. Example function trigger prints notification to the screen. After printing the notification, Aviso polls for new notifications until the user interrupts the script.