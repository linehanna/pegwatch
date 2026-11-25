# PegWatch

**Keeping watch over the peg.** A real-time stablecoin risk simulator.

PegWatch is built **twice**: once on **Google Cloud** and once on **Databricks**, followed by a measured comparison of the two platforms.

You play the risk officer of a fictional bank's stablecoin treasury. Live market data streams in. When a peg wobbles, volatility spikes or a payment looks unusual, you decide: hold, rebalance, pause settlement or block. An ML early-warning model and an AI agent advise you. You make the call, and every decision is written to an audit log.

> All client and payment data in this project is **synthetic**. Market and FX data comes from public sources. Nothing here is investment advice.

## Why two platforms?

Choosing a data platform is an architecture decision with real trade-offs. Instead of guessing, this project implements the same pipeline, same gold tables and same ML model on both platforms, measures them against fixed criteria, and documents the result.

## Architecture

```
Data sources ─► Ingestion ─► Bronze ─► Silver ─► Gold ─► ML + AI agent ─► Decision API ─► Game UI
             (built twice: platforms/gcp and platforms/databricks)        (shared, switchable backend)
```

| Layer | Google Cloud | Databricks |
|---|---|---|
| Live data | e2-micro VM, WebSocket collector | Scheduled micro-batch jobs |
| Batch jobs | Cloud Run jobs + Cloud Scheduler | Databricks Jobs |
| Storage | Cloud Storage + BigQuery | Delta tables, Unity Catalog |
| Transformations | BigQuery SQL | Lakeflow declarative pipeline |
| ML | BigQuery ML | MLflow + scikit-learn |
| IaC | Terraform | Databricks Asset Bundles |

Both platforms must produce identical gold tables (see `shared/` for the schema contract). The API selects a backend with `BACKEND=gcp` or `BACKEND=databricks`.

## Data sources

| Source | Data | Frequency |
|---|---|---|
| Coinbase Exchange WebSocket | Live prices and trades | Real-time |
| CoinGecko API (Demo) | Price history, stablecoin prices | Hourly / backfill |
| Riksbank SWEA API | SEK exchange rates, policy rate | Daily |
| ESMA interim MiCA register | Authorised stablecoin issuers and CASPs | Weekly |
| Synthetic generator | Fictional corporate clients and payments | Generated |

Market data provided by CoinGecko.

## Repository structure

```
shared/                 source clients, synthetic data generator, gold schema contract
platforms/gcp/          Terraform, Cloud Run jobs, BigQuery SQL, BigQuery ML
platforms/databricks/   Asset Bundle, pipeline, MLflow notebooks
api/                    C# .NET Decision API (switchable backend)
web/                    React + TypeScript game UI
docs/                   architecture, data sources, comparison log, final comparison
```

## Responsible AI

- The AI agent explains and recommends. It never executes an action on its own.
- Every recommendation and every human decision is logged with a timestamp and reason.
- Model performance (including where it was wrong) is shown in the UI.

## Cost

Target: **0 kr** on both platforms, using the Google Cloud free tier and Databricks Free Edition. Cost findings are tracked in `docs/comparison-log.md`.

## Status

🚧 Work in progress. See `docs/comparison-log.md` for progress and findings.
