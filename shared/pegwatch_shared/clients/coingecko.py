"""CoinGecko Demo API client.

Free Demo plan: ~10,000 calls/month, ~30-100 calls/min, history limited to the past 365 days.
Attribution required in the UI: "Data provided by CoinGecko".
Docs: https://docs.coingecko.com/demo/reference
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from ..assets import coingecko_ids
from ..http import RawRecord, Throttle, get_json, make_session

BASE_URL = "https://api.coingecko.com/api/v3"
MAX_HISTORY_DAYS = 365  # Demo plan limit


class CoinGeckoClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("COINGECKO_DEMO_API_KEY", "")
        if not self.api_key:
            raise ValueError("COINGECKO_DEMO_API_KEY is not set")
        self.session = make_session()
        self.session.headers["x-cg-demo-api-key"] = self.api_key
        self.throttle = Throttle(min_interval=2.5)  # stay well under the per-minute limit

    def _get(self, path: str, dataset: str, params: dict | None = None) -> RawRecord:
        self.throttle.wait()
        return get_json(self.session, f"{BASE_URL}{path}", source="coingecko", dataset=dataset, params=params)

    def ping(self) -> RawRecord:
        return self._get("/ping", "ping")

    def simple_price(self, ids: list[str] | None = None) -> RawRecord:
        """Current price in USD and EUR for all tracked assets, in ONE call."""
        return self._get(
            "/simple/price",
            "simple_price",
            {
                "ids": ",".join(ids or coingecko_ids()),
                "vs_currencies": "usd,eur",
                "include_24hr_vol": "true",
                "include_last_updated_at": "true",
                "precision": "full",
            },
        )

    def market_chart_range(self, coin_id: str, start: datetime, end: datetime, vs_currency: str = "usd") -> RawRecord:
        """Price, market cap and volume history between two times.

        Granularity is automatic: <=1 day = 5-minutely, 2-90 days = hourly, >90 days = daily.
        """
        oldest = datetime.now(timezone.utc).timestamp() - MAX_HISTORY_DAYS * 86400
        if start.timestamp() < oldest:
            raise ValueError(f"Demo plan only allows the past {MAX_HISTORY_DAYS} days of history")
        return self._get(
            f"/coins/{coin_id}/market_chart/range",
            "market_chart_range",
            {
                "vs_currency": vs_currency,
                "from": int(start.timestamp()),
                "to": int(end.timestamp()),
                "precision": "full",
            },
        )
