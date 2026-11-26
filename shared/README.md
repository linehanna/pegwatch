# pegwatch-shared

Code used by **both** platforms, so GCP and Databricks fetch exactly the same data the same way.

```
shared/
├── pegwatch_shared/
│   ├── assets.py          tracked assets and their ids per source
│   ├── http.py            retries, throttling, RawRecord (the bronze envelope)
│   └── clients/
│       ├── coingecko.py   prices + history (Demo key, 365 days of history)
│       ├── coinbase.py    REST tickers + candles (no key)
│       ├── coinbase_ws.py live WebSocket feed for the GCP VM (no key)
│       ├── riksbank.py    SEK exchange rates (key optional)
│       └── esma.py        MiCA register CSVs (no key, links discovered from ESMA's page)
├── schema/                gold schema contract + generated DDL
└── scripts/smoke_test.py  calls every source once
```

## Install and test locally

From the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e shared
python shared/scripts/smoke_test.py
```

Keys are read from `.env` (never commit it). Samples are written to `data/bronze/` (git-ignored).

## The bronze envelope

Every client returns `RawRecord` objects: the untouched source response plus metadata
(`source`, `dataset`, `endpoint`, `params`, `status_code`, `fetched_at`, `record_id`).
`RawRecord.bronze_path()` gives the same Hive-style path on both platforms:

```
coingecko/simple_price/dt=2026-11-26/hour=20/20261126T201503Z_ab12cd.json
```

## Known limits

- **CoinGecko Demo** only serves the past 365 days of history, so the March 2023 USDC depeg is out of reach. Training data for older events will come from Coinbase candles (USDT-USD etc.), which have no such limit.
- **Coinbase** has no USDC-USD pair (Coinbase treats USDC as USD). USDC prices come from CoinGecko.
- **Riksbank** without a key: 5 calls/minute, so the client waits ~13 s between calls.
- **ESMA** CSV file names change with each update; the client finds them on the MiCA page. If ESMA changes the page layout, `discover_csv_links()` will raise a clear error.
