"""ESMA interim MiCA register client.

ESMA publishes the register as a handful of CSV files linked from its MiCA page,
and the file names change with each update. So instead of hardcoding URLs, this
client reads the page and discovers the current CSV links.

Register files include: white papers, ART issuers, EMT issuers (stablecoins like
EURC/USDC), authorised CASPs and non-compliant entities.
"""

from __future__ import annotations

import os
import re
from urllib.parse import urljoin

from ..http import RawRecord, Throttle, make_session

MICA_PAGE = (
    "https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/"
    "markets-crypto-assets-regulation-mica"
)
CSV_LINK = re.compile(r'href="([^"]+\.csv)"', re.IGNORECASE)

# Keywords used to classify each discovered CSV by its file name
# Order matters: "ncasp" must be checked before "casp".
CATEGORIES = {
    "non_compliant": ("ncasp", "non-compliant", "noncompliant", "non_compliant"),
    "casp": ("casp",),
    "emt": ("emt",),
    "art": ("art",),
    "white_papers": ("othr", "other", "white"),
}


class EsmaMicaClient:
    def __init__(self, page_url: str | None = None) -> None:
        self.page_url = page_url or os.environ.get("ESMA_MICA_PAGE", MICA_PAGE)
        self.session = make_session()
        self.throttle = Throttle(min_interval=1.0)

    def discover_csv_links(self) -> dict[str, str]:
        """Return {category: url} for each register CSV found on the MiCA page."""
        self.throttle.wait()
        resp = self.session.get(self.page_url, timeout=30)
        resp.raise_for_status()
        links = {urljoin(self.page_url, href) for href in CSV_LINK.findall(resp.text)}
        if not links:
            raise RuntimeError(f"No CSV links found on {self.page_url}; the page layout may have changed")

        found: dict[str, str] = {}
        for url in sorted(links):
            name = url.rsplit("/", 1)[-1].lower()
            category = next(
                (cat for cat, keys in CATEGORIES.items() if any(k in name for k in keys)),
                f"other_{len(found)}",
            )
            found.setdefault(category, url)
        return found

    def download(self, category: str, url: str) -> RawRecord:
        self.throttle.wait()
        resp = self.session.get(url, timeout=60)
        resp.raise_for_status()
        resp.encoding = resp.encoding or "utf-8"
        return RawRecord(
            source="esma",
            dataset=f"mica_{category}",
            endpoint=url,
            params={"category": category},
            status_code=resp.status_code,
            payload=resp.text,
            content_type="csv",
        )

    def download_all(self) -> list[RawRecord]:
        return [self.download(cat, url) for cat, url in self.discover_csv_links().items()]
