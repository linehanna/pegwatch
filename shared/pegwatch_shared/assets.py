"""The assets PegWatch tracks, and their ids in each data source."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    asset_id: str                 # our id, used in every gold table
    symbol: str
    name: str
    asset_type: str               # "stablecoin" | "volatile"
    peg_currency: str | None      # "USD" | "EUR" | None
    issuer: str | None
    coingecko_id: str
    coinbase_product: str | None  # None when Coinbase has no direct USD pair


ASSETS: tuple[Asset, ...] = (
    Asset("usdc", "USDC", "USD Coin", "stablecoin", "USD", "Circle", "usd-coin", None),
    Asset("usdt", "USDT", "Tether", "stablecoin", "USD", "Tether", "tether", "USDT-USD"),
    Asset("eurc", "EURC", "Euro Coin", "stablecoin", "EUR", "Circle", "euro-coin", "EURC-USD"),
    Asset("btc", "BTC", "Bitcoin", "volatile", None, None, "bitcoin", "BTC-USD"),
    Asset("eth", "ETH", "Ethereum", "volatile", None, None, "ethereum", "ETH-USD"),
)

BY_ID = {a.asset_id: a for a in ASSETS}


def coingecko_ids() -> list[str]:
    return [a.coingecko_id for a in ASSETS]


def coinbase_products() -> list[str]:
    return [a.coinbase_product for a in ASSETS if a.coinbase_product]
