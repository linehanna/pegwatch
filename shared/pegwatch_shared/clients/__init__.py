"""One client per data source. All return RawRecord objects for the bronze layer."""

from .coinbase import CoinbaseClient
from .coingecko import CoinGeckoClient
from .esma import EsmaMicaClient
from .riksbank import RiksbankClient

__all__ = ["CoinbaseClient", "CoinGeckoClient", "EsmaMicaClient", "RiksbankClient"]
