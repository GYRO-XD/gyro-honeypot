"""
Fake service listeners for GYRO Honeypot.
Each listener speaks just enough of a protocol to look real, captures
whatever the connecting client sends (e.g. login attempts), then logs
and reports it. No real authentication ever succeeds - there's nothing
behind these ports but logging.
"""

import asyncio
import datetime


class HoneypotService:
    def __init__(self, name: str, port: int, banner: str,
                 event_logger, geoip_resolver, notifier, dashboard_state: dict):
        self.name = name
        self.port = port
        self.banner = banner
        self.logger = event_logger
        self.geoip = geoip_resolver
        self.notifier = notifier
        self.dashboard_state = dashboard_state  # shared dict for live table

    async def start(self):
        server = await asyncio.start_server(self._handle_client, "0.0.0.0", self.port)
        return server

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        ip = addr[0] if addr else "unknown"

        captured = ""
        try:
            if self.banner:
                writer.write(self.banner.encode(errors="ignore"))
                await writer.drain()

            # Give the client a short window to send data (e.g. login/creds/HTTP request)
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=5)
                captured = data.decode(errors="replace").strip()
            except asyncio.TimeoutError:
                captured = "(no data sent)"

            # Fake services never grant access - just close after "processing"
            name_lower = self.name.lower()
            if name_lower == "http":
                writer.write(b"HTTP/1.1 401 Unauthorized\r\nServer: nginx\r\n\r\n")
            elif name_lower in ("ssh", "telnet", "ftp"):
                writer.write(b"Login incorrect\r\n")
            await writer.drain()
        except (ConnectionResetError, BrokenPipeError):
            captured = captured or "(connection reset)"
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

        await self._record_event(ip, captured)

    async def _record_event(self, ip: str, captured: str):
        geo = await self.geoip.resolve(ip)

        event = {
            "ip": ip,
            "port": self.port,
            "service": self.name,
            "captured": captured,
            "country": geo.get("country"),
            "city": geo.get("city"),
            "isp": geo.get("isp"),
        }
        await self.logger.log_event(event)

        # update shared dashboard state
        key = f"{ip}:{self.port}"
        existing = self.dashboard_state.get(key)
        self.dashboard_state[key] = {
            "ip": ip,
            "service": self.name,
            "port": self.port,
            "country": geo.get("country", "?"),
            "city": geo.get("city", "?"),
            "last_seen": datetime.datetime.now().strftime("%H:%M:%S"),
            "hits": (existing["hits"] + 1) if existing else 1,
        }

        await self.notifier.send_alert(ip, self.port, self.name, geo, extra=captured)
