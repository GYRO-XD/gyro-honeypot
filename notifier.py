"""
Telegram alert notifier for GYRO Honeypot.
Rate-limited per source IP so a single script hammering a fake port
doesn't flood your phone with notifications.
"""

import aiohttp
import asyncio
import time


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = False,
                 rate_limit_seconds: int = 30):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled
        self.rate_limit_seconds = rate_limit_seconds
        self._last_sent = {}  # ip -> timestamp
        self._lock = asyncio.Lock()

    def _should_send(self, ip: str) -> bool:
        now = time.time()
        last = self._last_sent.get(ip, 0)
        if now - last >= self.rate_limit_seconds:
            self._last_sent[ip] = now
            return True
        return False

    async def send_alert(self, ip: str, port: int, service: str, geo: dict, extra: str = ""):
        if not self.enabled:
            return
        if not self._should_send(ip):
            return  # suppressed, too soon since last alert for this IP

        text = (
            f"🚨 *GYRO Honeypot Hit*\n"
            f"IP: `{ip}`\n"
            f"Service: `{service}` (port {port})\n"
            f"Location: {geo.get('city', '?')}, {geo.get('country', '?')}\n"
            f"ISP: {geo.get('isp', '?')}\n"
        )
        if extra:
            text += f"Detail: `{extra[:200]}`\n"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, data=payload):
                    pass  # fire-and-forget; alerting must never block the listener
        except (asyncio.TimeoutError, aiohttp.ClientError):
            pass
