#!/usr/bin/env python3
"""
GYRO Honeypot
A lightweight, Termux-friendly honeypot: fake services, connection logging,
IP geolocation, and Telegram alerting - built for authorized defensive use
on networks/devices you own or are explicitly permitted to monitor.

Usage:
    python honeypot.py                  # run with config.json defaults
    python honeypot.py --config my.json # use a custom config
    python honeypot.py --no-dashboard   # headless mode (good for nohup/tmux)
"""

import argparse
import asyncio
import json
import sys

from rich import print as rprint
from rich.panel import Panel

from core.logger import EventLogger
from core.geoip import GeoIPResolver
from core.notifier import TelegramNotifier
from core.listener import HoneypotService
from core.dashboard import Dashboard

BANNER = r"""
[bold red]  ______ __     ______  ____ 
 / ____// /_   / ____/ / __ \
/ / __ / __ \ / /     / / / /
/ /_/ // /_/ // /___  / /_/ /
\____//_.___/ \____/  \____/[/bold red]
[bold white]        Honeypot & Intrusion Logger[/bold white]
[dim]        by GYRO-XD -- authorized defensive use only[/dim]
"""


def load_config(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        rprint(f"[bold red]Config file not found:[/bold red] {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        rprint(f"[bold red]Invalid JSON in config:[/bold red] {e}")
        sys.exit(1)


async def main_async(config: dict, show_dashboard: bool):
    rprint(Panel(BANNER, border_style="red"))

    log_cfg = config["logging"]
    event_logger = EventLogger(log_cfg["log_dir"], log_cfg["log_file"])

    geo_cfg = config["geoip"]
    geoip_resolver = GeoIPResolver(geo_cfg["provider_url"], geo_cfg["enabled"])

    tg_cfg = config["telegram"]
    notifier = TelegramNotifier(
        tg_cfg["bot_token"], tg_cfg["chat_id"],
        enabled=tg_cfg["enabled"], rate_limit_seconds=tg_cfg["rate_limit_seconds"],
    )
    if tg_cfg["enabled"] and "PUT_YOUR" in tg_cfg["bot_token"]:
        rprint("[bold yellow]Warning:[/bold yellow] Telegram is enabled but bot_token looks unset. "
               "See README for setup. Disabling alerts for this run.")
        notifier.enabled = False

    dashboard_state: dict = {}
    servers = []

    for svc in config["services"]:
        service = HoneypotService(
            name=svc["name"], port=svc["port"], banner=svc.get("banner"),
            event_logger=event_logger, geoip_resolver=geoip_resolver,
            notifier=notifier, dashboard_state=dashboard_state,
        )
        try:
            server = await service.start()
            servers.append(server)
            rprint(f"[green]✓[/green] Fake [bold]{svc['name']}[/bold] service listening on port [bold]{svc['port']}[/bold]")
        except OSError as e:
            rprint(f"[bold red]✗[/bold red] Could not bind port {svc['port']} for {svc['name']}: {e}")

    if not servers:
        rprint("[bold red]No services could be started. Exiting.[/bold red]")
        return

    rprint("\n[dim]Logging to: " + f"{log_cfg['log_dir']}/{log_cfg['log_file']}" + "[/dim]")
    rprint("[dim]Press Ctrl+C to stop.[/dim]\n")

    tasks = [asyncio.create_task(s.serve_forever()) for s in servers]

    if show_dashboard:
        dash_cfg = config["dashboard"]
        dashboard = Dashboard(dashboard_state, dash_cfg["refresh_seconds"], dash_cfg["max_rows"])
        tasks.append(asyncio.create_task(dashboard.run()))

    await asyncio.gather(*tasks)


def main():
    parser = argparse.ArgumentParser(description="GYRO Honeypot - Termux-friendly intrusion logger")
    parser.add_argument("--config", default="config.json", help="Path to config JSON file")
    parser.add_argument("--no-dashboard", action="store_true", help="Run headless, no live table (good for background/tmux use)")
    args = parser.parse_args()

    config = load_config(args.config)

    try:
        asyncio.run(main_async(config, show_dashboard=not args.no_dashboard))
    except KeyboardInterrupt:
        rprint("\n[bold yellow]Shutting down GYRO Honeypot...[/bold yellow]")


if __name__ == "__main__":
    main()
