# GYRO Honeypot 🛡️

A lightweight, Termux-friendly honeypot and intrusion logger. Deploys fake
network services, logs every connection attempt, geolocates the source IP,
and sends real-time alerts to Telegram — all with a live `rich`-powered
terminal dashboard.

> ⚠️ **Authorized use only.** This tool is for monitoring devices/networks
> you own or are explicitly authorized to test (home lab, your own VPS,
> a CTF environment, a client engagement with signed authorization).
> Deploying it to intercept or monitor systems you don't control, or using
> logged credentials against real accounts, is illegal in most jurisdictions.
> This project logs *connection attempts against fake services* — it does
> not grant access to anything real.

## What it does

- Spins up fake **SSH**, **Telnet**, **FTP**, and **HTTP** listeners with
  realistic banners
- Captures whatever a connecting client sends (login attempts, HTTP
  requests, etc.) — nothing behind these ports ever succeeds
- Logs every event as structured JSON (`logs/events.jsonl`)
- Geolocates source IPs (country/city/ISP) via a free API, with caching
- Sends rate-limited Telegram alerts so you're notified without getting
  spammed by a single scanning script
- Live terminal dashboard showing active attackers, hit counts, and
  locations in real time

## Requirements

- Python 3.9+
- Termux (Android) or any Linux/macOS environment

## Installation (Termux)

```bash
pkg update && pkg upgrade
pkg install python git
git clone https://github.com/GYRO-XD/gyro-honeypot.git
cd gyro-honeypot
pip install -r requirements.txt
```

Optional but recommended on Android — prevent Termux from being killed by
battery optimization while the honeypot runs:

```bash
termux-wake-lock
```

## Telegram bot setup (optional but recommended)

1. Open Telegram, search for **@BotFather**, send `/newbot`, follow the
   prompts. You'll get a **bot token** (looks like `123456789:AAExxxxxxx`).
2. Start a chat with your new bot (search its username, hit Start).
3. Get your **chat ID**: message your bot anything, then visit
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser —
   your chat ID is in the JSON response under `message.chat.id`.
4. Edit `config.json`:

```json
"telegram": {
  "enabled": true,
  "bot_token": "123456789:AAExxxxxxx",
  "chat_id": "987654321",
  "rate_limit_seconds": 30
}
```

## Usage

```bash
# Run with live dashboard
python honeypot.py

# Run headless (recommended inside tmux/nohup for long-running sessions)
python honeypot.py --no-dashboard

# Use a custom config
python honeypot.py --config myconfig.json
```

Stop anytime with `Ctrl+C`.

## Configuring fake services

Edit `config.json` to add/remove/change ports:

```json
{"name": "ssh", "port": 2222, "banner": "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.4"}
```

> Note: Termux typically can't bind ports below 1024 without root. Default
> ports (2222, 2323, 2121, 8080) avoid this. If you want to expose these as
> the "real" 22/80/21 to the outside world, set up port forwarding on your
> router rather than trying to bind low ports directly.

## Reading logs

Logs are newline-delimited JSON — easy to process:

```bash
cat logs/events.jsonl | jq '.ip' | sort | uniq -c | sort -rn
```

Shows attacker IPs sorted by number of attempts.

## Project structure

```
gyro-honeypot/
├── honeypot.py        # entrypoint / CLI
├── config.json        # ports, services, telegram, geoip settings
├── core/
│   ├── listener.py     # fake service logic
│   ├── logger.py        # JSON event logging
│   ├── geoip.py          # IP geolocation + caching
│   ├── notifier.py       # Telegram alerts
│   └── dashboard.py      # live rich dashboard
├── logs/               # generated at runtime
└── requirements.txt
```

## Roadmap ideas

- [ ] SQLite backend option for querying historical hits
- [ ] Web dashboard (Flask/FastAPI) alongside terminal view
- [ ] Configurable fake login credentials that "succeed" to a fake shell
      (for deeper attacker behavior logging)
- [ ] Discord/Slack notifier alternatives
- [ ] Docker deployment option for VPS use

## License

MIT — use, modify, and learn from this freely. Attribution appreciated.

---
Built by **GYRO-XD**
