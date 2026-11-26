"""Call every PegWatch data source once and print what came back.

Run from the repo root (C:\\PegWatch):
    pip install -e shared
    python shared/scripts/smoke_test.py

Reads keys from .env. Saves one sample per source under data/bronze/ (git-ignored),
so you can open the files and see exactly what bronze will contain.
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env loader, so python-dotenv isn't required."""
    if not path.exists():
        print("!! No .env file found in the current folder. Run this from C:\\PegWatch.")
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()

from pegwatch_shared.assets import ASSETS, coinbase_products  # noqa: E402
from pegwatch_shared.clients import CoinbaseClient, CoinGeckoClient, EsmaMicaClient, RiksbankClient  # noqa: E402
from pegwatch_shared.http import write_local  # noqa: E402

results: dict[str, bool] = {}


def check(name: str):
    def decorator(fn):
        print(f"\n=== {name} ===")
        try:
            fn()
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            results[name] = False
            print(f"FAILED: {type(exc).__name__}: {exc}")
            if os.environ.get("PEGWATCH_DEBUG"):
                traceback.print_exc()
        return fn
    return decorator


@check("CoinGecko")
def _coingecko():
    cg = CoinGeckoClient()
    rec = cg.simple_price()
    for coin, data in rec.payload.items():
        print(f"  {coin:<10} USD {data.get('usd'):>14}   EUR {data.get('eur'):>14}")
    print(f"  saved -> {write_local(rec)}")

    end = datetime.now(timezone.utc)
    hist = cg.market_chart_range("usd-coin", end - timedelta(days=2), end)
    prices = hist.payload.get("prices", [])
    print(f"  USDC history, last 2 days: {len(prices)} points")
    print(f"  saved -> {write_local(hist)}")


@check("Coinbase")
def _coinbase():
    cb = CoinbaseClient()
    available = {p["id"] for p in cb.products().payload}
    for product in coinbase_products():
        status = "ok" if product in available else "NOT LISTED, remove from assets.py"
        print(f"  pair {product:<9} {status}")
    stable_pairs = sorted(p for p in available if p.split("-")[0] in {"USDC", "USDT", "EURC", "PYUSD", "DAI"})
    print(f"  stablecoin pairs on Coinbase: {', '.join(stable_pairs)}")

    rec = cb.ticker("BTC-USD")
    print(f"  BTC-USD last price: {rec.payload.get('price')}")
    print(f"  saved -> {write_local(rec)}")

    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    candles = cb.candles("BTC-USD", end - timedelta(minutes=10), end, granularity=60)
    print(f"  BTC-USD 1-minute candles, last 10 min: {len(candles.payload)}")


@check("Riksbank")
def _riksbank():
    rb = RiksbankClient()
    print(f"  using API key: {'yes' if rb.has_key else 'no (keyless: 5 calls/min, waits between calls)'}")
    for pair in ("USDSEK", "EURSEK"):
        rec = rb.latest(pair)
        print(f"  {pair}: {rec.payload.get('value')} (date {rec.payload.get('date')})")
    print(f"  saved -> {write_local(rec)}")


@check("ESMA MiCA register")
def _esma():
    esma = EsmaMicaClient()
    links = esma.discover_csv_links()
    for category, url in links.items():
        print(f"  {category:<14} {url}")
    if "emt" in links:
        rec = esma.download("emt", links["emt"])
        rows = rec.payload.count("\n")
        print(f"  EMT issuers file: ~{rows} rows")
        names = [a.issuer for a in ASSETS if a.issuer]
        for issuer in sorted(set(names)):
            print(f"  '{issuer}' mentioned in EMT register: {issuer.lower() in rec.payload.lower()}")
        print(f"  saved -> {write_local(rec)}")


print("\n=== Summary ===")
for name, ok in results.items():
    print(f"  {'OK  ' if ok else 'FAIL'} {name}")
sys.exit(0 if all(results.values()) else 1)
