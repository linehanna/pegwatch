"""Live Coinbase WebSocket feed, used by the always-on collector on the GCP VM.

Needs the optional dependency:  pip install "pegwatch-shared[live]"

Uses the `ticker_batch` channel: one update per product at most every 5 seconds,
which is plenty for risk monitoring and keeps data volumes small.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from ..assets import coinbase_products
from ..http import utc_now

WS_URL = "wss://ws-feed.exchange.coinbase.com"
log = logging.getLogger(__name__)


async def stream_ticker_batch(
    product_ids: list[str] | None = None,
    max_backoff: float = 60.0,
) -> AsyncIterator[dict[str, Any]]:
    """Yield ticker messages forever, reconnecting with backoff if the connection drops.

    Each yielded message gets `_received_at` (UTC) so gaps can be detected downstream.
    """
    import websockets  # imported here so the rest of the package works without it

    products = product_ids or coinbase_products()
    subscribe = {"type": "subscribe", "product_ids": products, "channels": ["ticker_batch"]}
    backoff = 1.0

    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=20) as ws:
                await ws.send(json.dumps(subscribe))
                log.info("Subscribed to %s", products)
                backoff = 1.0
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("type") == "error":
                        log.error("Coinbase error: %s", msg)
                        continue
                    if msg.get("type") in ("ticker", "ticker_batch"):
                        msg["_received_at"] = utc_now().isoformat()
                        yield msg
        except (OSError, websockets.ConnectionClosed) as exc:
            log.warning("Connection lost (%s); reconnecting in %.0fs", exc, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
