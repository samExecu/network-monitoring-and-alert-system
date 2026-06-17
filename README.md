# NetMon - Network Monitoring & Alert System

A network health monitor that keeps tabs on your hosts and services. It watches for problems, alerts you when something goes wrong, and keeps a log of everything that happens.
Built with Python. Works on Windows, macOS, and Linux.

> **Note:** This project is still being worked on. It's not finished yet and isn't ready to use in production. Stuff might break or change without warning.

---

## What's Done

- **Monitoring** - Pings hosts, checks if HTTP services are responding, and monitors specific ports
- **Problem detection** - Spots when hosts go down, latency gets bad, there's packet loss, HTTP errors happen, or ports randomly open/close
- **Alerts** - Sends notifications to Discord and email when things break
- **Database storage** - Keeps all the metrics and alert history in SQLite so you can look back at what happened
- **Scheduler** - Runs checks regularly on all your targets without blocking each other

---

## Tech Stack

| Part      | What we used                               |
| --------- | ------------------------------------------ |
| Monitor   | Python (ping), sockets, HTTP requests      |
| Scheduler | APScheduler - runs tasks on a timer        |
| Storage   | SQLite - simple database built into Python |
| Alerts    | Discord Webhooks, Gmail SMTP               |
| Detection | Custom code that spots problems            |

---

## What's Included

- **Ping monitor** - Checks if hosts respond and how fast
- **HTTP monitor** - Tests web services and measures response time
- **Port monitor** - Watches specific ports for changes
- **8 different detectors** - Looks for host downtime, latency spikes, packet loss, bad HTTP responses, slow responses, port changes, and weird behavior patterns
- **Multi-channel alerts** - Gets you notifications on Discord and email

---

## What It Looks Like

### Ping Monitor

![Ping Monitor Screenshot](docs/ping-monitor.png)

### HTTP Monitor

![HTTP Monitor Screenshot](docs/http-monitor.png)

### Port Monitor

![Port Monitor Screenshot](docs/port-monitor.png)

### Discord Alerts

![Discord Alert Screenshot](docs/discord-alert.png)

### Email Alerts

![Email Alert Screenshot](docs/email-alert.png)

---

## Getting Started

1. **Set up Python** - Make sure you have Python 3.9+ installed
2. **Install dependencies** - Run `pip install -r requirements.txt`
3. **Configure targets** - Edit `config.py` and add the hosts you want to monitor
4. **Set up alerts** - Add your Discord webhook and email settings to a `.env` file
5. **Run it** - Execute each file seperately to test the features out

> **Note:** Don't run scheduler.py and anamoly.py seperately, it's still being configured

All your metrics and alerts get saved to the database, and you can look back at what happened whenever you want.

---

## Typography

This project uses **Apfel Grotezk**, a high-quality open-source typeface designed by Collletttivo.

**Font License:** Apfel Grotezk is licensed under the [SIL Open Font License (OFL) v1.1](https://scripts.sil.org/OFL)

- **Author:** Collletttivo (https://www.collletttivo.it/)
- **License:** SIL Open Font License v1.1
- **Font Files Location:** `dashboard/templates/fonts/apfel-grotezk-main/`

---

## The Team

1. Bikram Timalsina
2. Karan Bhatt
3. Rojan Tamang
4. Sushant Ale Magar
