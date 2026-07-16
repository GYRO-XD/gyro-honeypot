"""
Live terminal dashboard for GYRO Honeypot, powered by rich.
Shows most-recently-active source IPs across all fake services.
"""

import asyncio
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.console import Console


class Dashboard:
    def __init__(self, dashboard_state: dict, refresh_seconds: int = 2, max_rows: int = 20):
        self.state = dashboard_state
        self.refresh_seconds = refresh_seconds
        self.max_rows = max_rows
        self.console = Console()

    def _build_table(self) -> Table:
        table = Table(title="🛡️  GYRO Honeypot — Live Intrusion Log", expand=True)
        table.add_column("IP", style="bold red")
        table.add_column("Service", style="cyan")
        table.add_column("Port", justify="right")
        table.add_column("Location", style="yellow")
        table.add_column("Hits", justify="right", style="magenta")
        table.add_column("Last Seen", style="green")

        rows = sorted(self.state.values(), key=lambda r: r["last_seen"], reverse=True)
        for row in rows[: self.max_rows]:
            location = f"{row['city']}, {row['country']}"
            table.add_row(
                row["ip"], row["service"], str(row["port"]),
                location, str(row["hits"]), row["last_seen"],
            )
        return table

    async def run(self):
        with Live(self._build_table(), refresh_per_second=1, console=self.console) as live:
            while True:
                await asyncio.sleep(self.refresh_seconds)
                live.update(self._build_table())
