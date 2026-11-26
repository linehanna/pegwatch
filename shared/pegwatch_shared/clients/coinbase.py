"""Coinbase Exchange public market data (REST). No API key needed.

Used by Databricks (scheduled micro-batches) and for history backfills.
The live WebSocket version used on the GCP VM is in coinbase_ws.py.
Docs: https://docs.cdp.coinbase.com/exchange/reference
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..assets import coinbase_products
from ..http import RawRecord, Throttle, get_json, make_session

BASE_URL = "https://api.exchange.coinbase.com"
MAX_CANDLES_PER_REQUEST = 300
VALID_GRANULARITIES = (60, 300, 900, 3600, 21600, 86400)  # seconds


class CoinbaseClient:
    def __init__(self) -> None:
        self.session = make_session()
        self.throttle = Throttle(min_interval=0.2)  # public limit is ~10 req/s

    def _get(self, path: str, dataset: str, params: dict | None = None) -> RawRecord:
        self.throttle.wait()
        return get_json(self.session, f"{BASE_URL}{path}", source="coinbase", dataset=dataset, params=params)

    def products(self) -> RawRecord:
        """All trading pairs. Used to check which of our pairs exist."""
        return self._get("/products", "products")

    def ticker(self, product_id: str) -> RawRecord:
        """Latest trade price, best bid/ask and 24h volume for one pair."""
        return self._get(f"/products/{product_id}/ticker", "ticker", {"product": product_id})

    def tickers(self, product_ids: list[str] | None = None) -> list[RawRecord]:
        return [self.ticker(p) for p in (product_ids or coinbase_products())]

    def candles(self, product_id: str, start: datetime, end: datetime, granularity: int = 60) -> RawRecord:
        """OHLCV candles: [time, low, high, open, close, volume], newest first. Max 300 per call."""
        if granularity not in VALID_GRANULARITIES:
            raise ValueError(f"granularity must be one of {VALID_GRANULARITIES}")
        if (end - start).total_seconds() / granularity > MAX_CANDLES_PER_REQUEST:
            raise ValueError("Range too large for one request; use candles_range()")
        return self._get(
            f"/products/{product_id}/candles",
            "candles",
            {"granularity": granularity, "start": start.isoformat(), "end": end.isoformat(), "product": product_id},
        )

    def candles_range(self, product_id: str, start: datetime, end: datetime, granularity: int = 60) -> list[RawRecord]:
        """Any range, split into 300-candle requests. Good for history backfills."""
        step = timedelta(seconds=granularity * MAX_CANDLES_PER_REQUEST)
        records, cursor = [], start
        while cursor < end:
            chunk_end = min(cursor + step, end)
            records.append(self.candles(product_id, cursor, chunk_end, granularity))
            cursor = chunk_end
        return records
