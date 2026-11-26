# Gold schema contract

`gold_contract.yaml` defines the gold layer that **both** platforms must produce. The API and the game only read gold, so if both platforms honour this contract, the backend can be switched with `BACKEND=gcp` or `BACKEND=databricks`.

## Tables

| Table | Grain | Used for |
|---|---|---|
| `dim_asset` | One row per asset | Asset list, peg currency, MiCA status |
| `fct_price_minute` | Asset × minute | Live charts, peg deviation |
| `fct_risk_hourly` | Asset × hour | Risk score, game difficulty, ML features |
| `fct_depeg_prediction` | Asset × prediction time | ML early warning |
| `fct_alert` | One row per alert | Situations the player must decide on |
| `dim_client` | One row per synthetic client | Payments context |
| `fct_payment` | One row per synthetic payment | Routing, MiCA checks, anomaly flags |
| `fct_fx_daily` | Currency pair × day | SEK conversion |

## Rules

- All timestamps are **UTC**.
- Money uses **NUMERIC** (BigQuery) = **DECIMAL(38,9)** (Databricks), never floats.
- Peg deviation is in **basis points**: `(price_in_peg - 1) * 10000`. A USDC price of $0.998 is -20 bps.
- Every table has a `platform` column (`gcp` or `databricks`), so outputs can be compared side by side.
- `fct_alert.alert_id` is a deterministic hash of its inputs, so the same alert gets the same id on both platforms.
- All client and payment data is **synthetic** (`is_synthetic = true`).

## Changing the contract

1. Edit `gold_contract.yaml` and bump `version`
2. Run `python shared/schema/generate_ddl.py` (needs `pip install pyyaml`)
3. Commit the contract **and** the regenerated files in `generated/`
4. Apply the new SQL on both platforms

Never edit the files in `generated/` by hand.

## Type mapping

| Contract | BigQuery | Databricks |
|---|---|---|
| STRING | STRING | STRING |
| INT64 | INT64 | BIGINT |
| FLOAT64 | FLOAT64 | DOUBLE |
| NUMERIC | NUMERIC | DECIMAL(38,9) |
| BOOL | BOOL | BOOLEAN |
| DATE | DATE | DATE |
| TIMESTAMP | TIMESTAMP | TIMESTAMP |

BigQuery tables are partitioned by day on their time column and clustered by key. Databricks tables use liquid clustering on the key plus the time column.
