"""Bronze ingestion jobs, shared by both platforms.

    python -m pegwatch_shared.ingest --job market_hourly --sink gs://pegwatch-bronze-9aa513
    python -m pegwatch_shared.ingest --job fx_daily      --sink /Volumes/workspace/pegwatch_bronze/raw
    python -m pegwatch_shared.ingest --job mica_weekly   --sink data/bronze

Jobs
- market_hourly: CoinGecko snapshot + short history for assets Coinbase lacks (USDC),
                 Coinbase 1-minute candles for the last 65 minutes (overlap is deduplicated in silver)
- fx_daily:      Riksbank USD/SEK and EUR/SEK
- mica_weekly:   ESMA interim MiCA register (all five CSVs)

Each source is fetched independently: if one fails, the others are still written,
and the job exits with code 1 so the scheduler marks the run as failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from .assets import ASSETS
from .clients import CoinbaseClient, CoinGeckoClient, EsmaMicaClient, RiksbankClient
from .sinks import Sink, sink_from_uri

CANDLE_LOOKBACK = timedelta(minutes=65)


def log(event: str, **fields) -> None:
    """One JSON line per event: readable locally, structured in Cloud Logging and Databricks."""
    print(json.dumps({"event": event, "ts": datetime.now(timezone.utc).isoformat(), **fields}), flush=True)


class Run:
    def __init__(self, job: str, sink: Sink) -> None:
        self.job, self.sink = job, sink
        self.written = 0
        self.errors: list[str] = []

    def step(self, name: str, fn: Callable[[], list]) -> None:
        started = time.monotonic()
        try:
            records = fn()
            paths = [self.sink.write(r) for r in records]
            self.written += len(paths)
            log("step_ok", job=self.job, step=name, records=len(paths), seconds=round(time.monotonic() - started, 2))
        except Exception as exc:  # noqa: BLE001 - one source failing must not stop the others
            self.errors.append(f"{name}: {type(exc).__name__}: {exc}")
            log("step_failed", job=self.job, step=name, error=f"{type(exc).__name__}: {exc}")


def market_hourly(run: Run) -> None:
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    cg = CoinGeckoClient()
    run.step("coingecko_simple_price", lambda: [cg.simple_price()])
    for asset in ASSETS:
        if asset.coinbase_product is None:  # e.g. USDC: no direct USD pair on Coinbase
            run.step(
                f"coingecko_history_{asset.asset_id}",
                lambda a=asset: [cg.market_chart_range(a.coingecko_id, now - timedelta(hours=2), now)],
            )

    cb = CoinbaseClient()
    for asset in ASSETS:
        if asset.coinbase_product:
            run.step(
                f"coinbase_candles_{asset.asset_id}",
                lambda a=asset: [cb.candles(a.coinbase_product, now - CANDLE_LOOKBACK, now, granularity=60)],
            )


def fx_daily(run: Run) -> None:
    rb = RiksbankClient()
    for pair in ("USDSEK", "EURSEK"):
        run.step(f"riksbank_{pair.lower()}", lambda p=pair: [rb.latest(p)])


def mica_weekly(run: Run) -> None:
    esma = EsmaMicaClient()
    run.step("esma_mica_register", esma.download_all)


JOBS: dict[str, Callable[[Run], None]] = {
    "market_hourly": market_hourly,
    "fx_daily": fx_daily,
    "mica_weekly": mica_weekly,
}


def load_dotenv_if_present(path: str = ".env") -> None:
    """Local runs only: read keys from .env. On GCP and Databricks keys come from secrets."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_present()
    parser = argparse.ArgumentParser(description="PegWatch bronze ingestion")
    parser.add_argument("--job", required=True, choices=sorted(JOBS))
    parser.add_argument(
        "--sink",
        default=os.environ.get("PEGWATCH_BRONZE_URI", "data/bronze"),
        help="gs://bucket[/prefix] or a folder path (default: $PEGWATCH_BRONZE_URI or data/bronze)",
    )
    args = parser.parse_args(argv)

    sink = sink_from_uri(args.sink)
    run = Run(args.job, sink)
    log("job_started", job=args.job, sink=repr(sink))
    started = time.monotonic()
    JOBS[args.job](run)
    log(
        "job_finished",
        job=args.job,
        records=run.written,
        errors=len(run.errors),
        seconds=round(time.monotonic() - started, 2),
    )
    return 1 if run.errors else 0


if __name__ == "__main__":
    sys.exit(main())
