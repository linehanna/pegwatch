"""HTTP helpers shared by all clients: retries, throttling and the raw record envelope.

Every client returns RawRecord objects. A RawRecord is exactly what the source sent,
plus metadata about how and when it was fetched. That is what lands in bronze.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "PegWatch/0.1 (portfolio project; github.com/linehanna/pegwatch)"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_session(total_retries: int = 4, backoff: float = 1.5) -> requests.Session:
    """A requests session that retries on 429 and 5xx with exponential backoff."""
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = USER_AGENT
    return session


class Throttle:
    """Keeps at least `min_interval` seconds between calls (for strict rate limits)."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        delay = self._last + self.min_interval - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self._last = time.monotonic()


@dataclass
class RawRecord:
    source: str                    # coingecko | coinbase | riksbank | esma
    dataset: str                   # e.g. simple_price, candles, fx_latest
    endpoint: str
    params: dict[str, Any]
    status_code: int
    payload: Any                   # parsed JSON, or text for CSV sources
    content_type: str = "json"     # json | csv
    fetched_at: str = field(default_factory=lambda: utc_now().isoformat())
    record_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def bronze_path(self) -> str:
        """Hive-style path, the same on GCS and in a Databricks volume.

        e.g. coingecko/simple_price/dt=2026-11-26/hour=20/20261126T201503Z_ab12cd.json
        """
        ts = datetime.fromisoformat(self.fetched_at)
        stamp = ts.strftime("%Y%m%dT%H%M%SZ")
        return (
            f"{self.source}/{self.dataset}/dt={ts:%Y-%m-%d}/hour={ts:%H}/"
            f"{stamp}_{self.record_id[:6]}.json"
        )


def get_json(
    session: requests.Session,
    url: str,
    *,
    source: str,
    dataset: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 20,
) -> RawRecord:
    resp = session.get(url, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return RawRecord(
        source=source,
        dataset=dataset,
        endpoint=url,
        params=params or {},
        status_code=resp.status_code,
        payload=resp.json(),
    )


def write_local(record: RawRecord, root: str | Path = "data/bronze") -> Path:
    """Write a record to a local folder using the bronze path layout (for testing)."""
    path = Path(root) / record.bronze_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
