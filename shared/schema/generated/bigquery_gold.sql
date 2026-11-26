-- GENERATED from shared/schema/gold_contract.yaml (contract v1). Do not edit by hand.

-- Dataset pegwatch_gold is created by Terraform (platforms/gcp/infra).

CREATE TABLE IF NOT EXISTS `pegwatch.pegwatch_gold.dim_asset` (
  asset_id STRING NOT NULL OPTIONS(description='Lowercase id, e.g. usdc, eurc, btc'),
  symbol STRING NOT NULL OPTIONS(description='Ticker, e.g. USDC'),
  name STRING NOT NULL,
  asset_type STRING NOT NULL OPTIONS(description='stablecoin | volatile'),
  peg_currency STRING OPTIONS(description='USD | EUR, null for volatile assets'),
  issuer STRING,
  mica_authorised BOOL OPTIONS(description='Issuer found in ESMA MiCA register'),
  mica_checked_at TIMESTAMP,
  platform STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL
)
CLUSTER BY asset_id
OPTIONS(description='One row per tracked asset, with its MiCA status.');

CREATE TABLE IF NOT EXISTS `pegwatch.pegwatch_gold.fct_price_minute` (
  asset_id STRING NOT NULL,
  ts_minute TIMESTAMP NOT NULL OPTIONS(description='Start of the minute, UTC'),
  price_usd NUMERIC NOT NULL,
  price_sek NUMERIC OPTIONS(description='Converted with latest Riksbank USD/SEK'),
  price_in_peg NUMERIC OPTIONS(description='Price in the asset\'s peg currency, null for volatile'),
  peg_deviation_bps FLOAT64 OPTIONS(description='(price_in_peg - 1) * 10000'),
  volume_usd NUMERIC,
  source STRING NOT NULL OPTIONS(description='coinbase | coingecko'),
  platform STRING NOT NULL,
  ingested_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(ts_minute)
CLUSTER BY asset_id
OPTIONS(description='One row per asset per minute. Prices in USD and SEK, plus peg deviation for stablecoins.');

CREATE TABLE IF NOT EXISTS `pegwatch.pegwatch_gold.fct_risk_hourly` (
  asset_id STRING NOT NULL,
  ts_hour TIMESTAMP NOT NULL,
  avg_peg_dev_bps FLOAT64,
  max_abs_peg_dev_bps FLOAT64,
  volatility_1h FLOAT64 OPTIONS(description='Std dev of 1-minute log returns'),
  volatility_24h FLOAT64,
  volume_usd_1h NUMERIC,
  risk_score INT64 NOT NULL OPTIONS(description='0-100, rule-based'),
  risk_level STRING NOT NULL OPTIONS(description='LOW | MEDIUM | HIGH'),
  platform STRING NOT NULL,
  computed_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(ts_hour)
CLUSTER BY asset_id
OPTIONS(description='Hourly risk metrics per asset. Feeds the game, the dashboard and the ML model.');

CREATE TABLE IF NOT EXISTS `pegwatch.pegwatch_gold.fct_depeg_prediction` (
  asset_id STRING NOT NULL,
  ts TIMESTAMP NOT NULL OPTIONS(description='Time the prediction is for'),
  prob_depeg_60m FLOAT64 NOT NULL OPTIONS(description='0.0-1.0'),
  predicted_depeg BOOL NOT NULL OPTIONS(description='prob_depeg_60m >= threshold'),
  threshold FLOAT64 NOT NULL,
  model_name STRING NOT NULL,
  model_version STRING NOT NULL,
  platform STRING NOT NULL,
  predicted_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(ts)
CLUSTER BY asset_id
OPTIONS(description='ML early-warning output. Probability that a stablecoin depegs within the next 60 minutes.');

CREATE TABLE IF NOT EXISTS `pegwatch.pegwatch_gold.fct_alert` (
  alert_id STRING NOT NULL OPTIONS(description='Deterministic hash, same alert = same id on both platforms'),
  asset_id STRING,
  payment_id STRING OPTIONS(description='Set for payment-related alerts'),
  ts TIMESTAMP NOT NULL,
  alert_type STRING NOT NULL OPTIONS(description='DEPEG | VOLATILITY | PAYMENT_ANOMALY | MICA_BREACH'),
  severity STRING NOT NULL OPTIONS(description='LOW | MEDIUM | HIGH'),
  metric_value FLOAT64,
  threshold FLOAT64,
  platform STRING NOT NULL,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(ts)
CLUSTER BY asset_id, alert_type
OPTIONS(description='Events the risk officer must react to in the game.');

CREATE TABLE IF NOT EXISTS `pegwatch.pegwatch_gold.dim_client` (
  client_id STRING NOT NULL,
  company_name STRING NOT NULL,
  country STRING NOT NULL OPTIONS(description='ISO 3166-1 alpha-2'),
  segment STRING NOT NULL OPTIONS(description='SME | MID | LARGE'),
  is_synthetic BOOL NOT NULL,
  platform STRING NOT NULL
)
CLUSTER BY client_id
OPTIONS(description='Synthetic corporate clients. All data is fictional.');

CREATE TABLE IF NOT EXISTS `pegwatch.pegwatch_gold.fct_payment` (
  payment_id STRING NOT NULL,
  client_id STRING NOT NULL,
  ts TIMESTAMP NOT NULL,
  amount NUMERIC NOT NULL,
  currency STRING NOT NULL OPTIONS(description='EUR | USD | SEK'),
  amount_sek NUMERIC,
  rail STRING NOT NULL OPTIONS(description='SEPA | SWIFT | STABLECOIN'),
  asset_id STRING OPTIONS(description='Set when rail = STABLECOIN'),
  provider STRING OPTIONS(description='Crypto-asset service provider used'),
  provider_mica_authorised BOOL,
  anomaly_score FLOAT64,
  is_synthetic BOOL NOT NULL,
  platform STRING NOT NULL
)
PARTITION BY DATE(ts)
CLUSTER BY client_id
OPTIONS(description='Synthetic cross-border payments, with routing and compliance flags.');

CREATE TABLE IF NOT EXISTS `pegwatch.pegwatch_gold.fct_fx_daily` (
  rate_date DATE NOT NULL,
  currency_pair STRING NOT NULL OPTIONS(description='e.g. USDSEK, EURSEK'),
  rate NUMERIC NOT NULL OPTIONS(description='SEK per 1 unit of foreign currency'),
  source STRING NOT NULL,
  platform STRING NOT NULL
)
PARTITION BY rate_date
CLUSTER BY currency_pair
OPTIONS(description='Riksbank exchange rates used for SEK conversion.');

