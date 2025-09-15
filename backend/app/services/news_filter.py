# backend/app/services/news_filter.py

import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("NewsFilter")

class NewsFilter:
    """Filters trades based on high-impact news from Forex Factory JSON feed."""

    def __init__(self):
        self.feed_url = "https://nfs.faireconomy.media/ff_calendar_this_week.json"
        self.window_minutes = 30  # Time window around trade timestamp
        self.high_impact_levels = {"High"}

    async def is_safe(self, symbol: str, ts: int) -> bool:
        try:
            currency = self._extract_currency(symbol)
            dt = datetime.utcfromtimestamp(ts)
            start = dt - timedelta(minutes=self.window_minutes)
            end = dt + timedelta(minutes=self.window_minutes)

            events = await self._fetch_news()
            for event in events:
                if self._is_relevant(event, currency, start, end):
                    logger.info(f"Blocked trade due to news: {event['title']}")
                    return False
            return True

        except Exception as e:
            logger.warning(f"News filter failed: {e}")
            return True  # Fail-safe: allow trade if filter fails

    async def _fetch_news(self) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.feed_url)
            response.raise_for_status()
            return response.json()

    def _is_relevant(self, event: dict, currency: str, start: datetime, end: datetime) -> bool:
        try:
            event_currency = event.get("currency", "")
            impact = event.get("impact", "")
            timestamp = int(event.get("timestamp", 0))
            event_time = datetime.utcfromtimestamp(timestamp)

            return (
                event_currency == currency and
                impact in self.high_impact_levels and
                start <= event_time <= end
            )
        except Exception:
            return False

    def _extract_currency(self, symbol: str) -> str:
        # e.g., "EURUSD" → "USD"
        return symbol[3:6].upper()
