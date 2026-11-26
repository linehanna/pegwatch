"""Riksbank SWEA API client: SEK exchange rates and policy rate.

The API key is OPTIONAL:
- without key: 5 calls/minute, 1,000 calls/day per IP (enough for a daily job)
- with key:    200 calls/minute, 30,000 calls/week
Rates are indicative and published on Swedish banking days. Not for transactions.
Docs: https://developer.api.riksbank.se
"""

from __future__ import annotations

import os
from datetime import date

from ..http import RawRecord, Throttle, get_json, make_session

BASE_URL = "https://api.riksbank.se/swea/v1"

# Series ids: SEK per 1 unit of foreign currency
SERIES = {
    "USDSEK": "SEKUSDPMI",
    "EURSEK": "SEKEURPMI",
}


class RiksbankClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("RIKSBANK_API_KEY", "")
        self.session = make_session()
        if self.api_key:
            self.session.headers["Ocp-Apim-Subscription-Key"] = self.api_key
            self.throttle = Throttle(min_interval=0.4)
        else:
            self.throttle = Throttle(min_interval=13)  # keyless limit: 5 calls/minute

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    def _get(self, path: str, dataset: str, params: dict | None = None) -> RawRecord:
        self.throttle.wait()
        return get_json(self.session, f"{BASE_URL}{path}", source="riksbank", dataset=dataset, params=params)

    def latest(self, pair: str) -> RawRecord:
        """Latest published rate for e.g. 'USDSEK'."""
        series = SERIES[pair]
        record = self._get(f"/Observations/Latest/{series}", "fx_latest")
        record.params = {"pair": pair, "series": series}
        return record

    def history(self, pair: str, start: date, end: date) -> RawRecord:
        """All published rates between two dates (inclusive)."""
        series = SERIES[pair]
        record = self._get(f"/Observations/{series}/{start.isoformat()}/{end.isoformat()}", "fx_history")
        record.params = {"pair": pair, "series": series, "from": start.isoformat(), "to": end.isoformat()}
        return record
