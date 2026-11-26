-- GENERATED from shared/schema/gold_contract.yaml (contract v1). Do not edit by hand.

CREATE SCHEMA IF NOT EXISTS workspace.pegwatch_gold;

CREATE TABLE IF NOT EXISTS workspace.pegwatch_gold.dim_asset (
  asset_id STRING NOT NULL COMMENT 'Lowercase id, e.g. usdc, eurc, btc',
  symbol STRING NOT NULL COMMENT 'Ticker, e.g. USDC',
  name STRING NOT NULL,
  asset_type STRING NOT NULL COMMENT 'stablecoin | volatile',
  peg_currency STRING COMMENT 'USD | EUR, null for volatile assets',
  issuer STRING,
  mica_authorised BOOLEAN COMMENT 'Issuer found in ESMA MiCA register',
  mica_checked_at TIMESTAMP,
  platform STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL
)
USING DELTA
CLUSTER BY (asset_id)
COMMENT 'One row per tracked asset, with its MiCA status.';

CREATE TABLE IF NOT EXISTS workspace.pegwatch_gold.fct_price_minute (
  asset_id STRING NOT NULL,
  ts_minute TIMESTAMP NOT NULL COMMENT 'Start of the minute, UTC',
  price_usd DECIMAL(38,9) NOT NULL,
  price_sek DECIMAL(38,9) COMMENT 'Converted with latest Riksbank USD/SEK',
  price_in_peg DECIMAL(38,9) COMMENT 'Price in the asset\'s peg currency, null for volatile',
  peg_deviation_bps DOUBLE COMMENT '(price_in_peg - 1) * 10000',
  volume_usd DECIMAL(38,9),
  source STRING NOT NULL COMMENT 'coinbase | coingecko',
  platform STRING NOT NULL,
  ingested_at TIMESTAMP NOT NULL
)
USING DELTA
CLUSTER BY (asset_id, ts_minute)
COMMENT 'One row per asset per minute. Prices in USD and SEK, plus peg deviation for stablecoins.';

CREATE TABLE IF NOT EXISTS workspace.pegwatch_gold.fct_risk_hourly (
  asset_id STRING NOT NULL,
  ts_hour TIMESTAMP NOT NULL,
  avg_peg_dev_bps DOUBLE,
  max_abs_peg_dev_bps DOUBLE,
  volatility_1h DOUBLE COMMENT 'Std dev of 1-minute log returns',
  volatility_24h DOUBLE,
  volume_usd_1h DECIMAL(38,9),
  risk_score BIGINT NOT NULL COMMENT '0-100, rule-based',
  risk_level STRING NOT NULL COMMENT 'LOW | MEDIUM | HIGH',
  platform STRING NOT NULL,
  computed_at TIMESTAMP NOT NULL
)
USING DELTA
CLUSTER BY (asset_id, ts_hour)
COMMENT 'Hourly risk metrics per asset. Feeds the game, the dashboard and the ML model.';

CREATE TABLE IF NOT EXISTS workspace.pegwatch_gold.fct_depeg_prediction (
  asset_id STRING NOT NULL,
  ts TIMESTAMP NOT NULL COMMENT 'Time the prediction is for',
  prob_depeg_60m DOUBLE NOT NULL COMMENT '0.0-1.0',
  predicted_depeg BOOLEAN NOT NULL COMMENT 'prob_depeg_60m >= threshold',
  threshold DOUBLE NOT NULL,
  model_name STRING NOT NULL,
  model_version STRING NOT NULL,
  platform STRING NOT NULL,
  predicted_at TIMESTAMP NOT NULL
)
USING DELTA
CLUSTER BY (asset_id, ts)
COMMENT 'ML early-warning output. Probability that a stablecoin depegs within the next 60 minutes.';

CREATE TABLE IF NOT EXISTS workspace.pegwatch_gold.fct_alert (
  alert_id STRING NOT NULL COMMENT 'Deterministic hash, same alert = same id on both platforms',
  asset_id STRING,
  payment_id STRING COMMENT 'Set for payment-related alerts',
  ts TIMESTAMP NOT NULL,
  alert_type STRING NOT NULL COMMENT 'DEPEG | VOLATILITY | PAYMENT_ANOMALY | MICA_BREACH',
  severity STRING NOT NULL COMMENT 'LOW | MEDIUM | HIGH',
  metric_value DOUBLE,
  threshold DOUBLE,
  platform STRING NOT NULL,
  created_at TIMESTAMP NOT NULL
)
USING DELTA
CLUSTER BY (asset_id, alert_type, ts)
COMMENT 'Events the risk officer must react to in the game.';

CREATE TABLE IF NOT EXISTS workspace.pegwatch_gold.dim_client (
  client_id STRING NOT NULL,
  company_name STRING NOT NULL,
  country STRING NOT NULL COMMENT 'ISO 3166-1 alpha-2',
  segment STRING NOT NULL COMMENT 'SME | MID | LARGE',
  is_synthetic BOOLEAN NOT NULL,
  platform STRING NOT NULL
)
USING DELTA
CLUSTER BY (client_id)
COMMENT 'Synthetic corporate clients. All data is fictional.';

CREATE TABLE IF NOT EXISTS workspace.pegwatch_gold.fct_payment (
  payment_id STRING NOT NULL,
  client_id STRING NOT NULL,
  ts TIMESTAMP NOT NULL,
  amount DECIMAL(38,9) NOT NULL,
  currency STRING NOT NULL COMMENT 'EUR | USD | SEK',
  amount_sek DECIMAL(38,9),
  rail STRING NOT NULL COMMENT 'SEPA | SWIFT | STABLECOIN',
  asset_id STRING COMMENT 'Set when rail = STABLECOIN',
  provider STRING COMMENT 'Crypto-asset service provider used',
  provider_mica_authorised BOOLEAN,
  anomaly_score DOUBLE,
  is_synthetic BOOLEAN NOT NULL,
  platform STRING NOT NULL
)
USING DELTA
CLUSTER BY (client_id, ts)
COMMENT 'Synthetic cross-border payments, with routing and compliance flags.';

CREATE TABLE IF NOT EXISTS workspace.pegwatch_gold.fct_fx_daily (
  rate_date DATE NOT NULL,
  currency_pair STRING NOT NULL COMMENT 'e.g. USDSEK, EURSEK',
  rate DECIMAL(38,9) NOT NULL COMMENT 'SEK per 1 unit of foreign currency',
  source STRING NOT NULL,
  platform STRING NOT NULL
)
USING DELTA
CLUSTER BY (currency_pair, rate_date)
COMMENT 'Riksbank exchange rates used for SEK conversion.';

