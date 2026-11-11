"""
eurostat_client.py
==================
Client to download EU external-trade data from the public Eurostat API
(Comext, dataset DS-045409: EU trade since 1988 by HS product).

IMPORTANT about the endpoint:
    Datasets with the "DS-" prefix come from the Comext database and use a
    DEDICATED endpoint, different from the general one:
        Comext:  https://ec.europa.eu/eurostat/api/comext/dissemination/...
        General: https://ec.europa.eu/eurostat/api/dissemination/...
    You must use the Comext endpoint or the API returns 404.

Real dataset dimensions (exact names the API expects):
    freq        -> "A" (annual), "M" (monthly)
    reporter    -> declaring country, e.g. "ES"
    partner     -> partner country, e.g. "CN"
    product     -> HS code, e.g. "9401"
    flow        -> "1" (import) / "2" (export)
    indicators  -> "VALUE_IN_EUROS" or "QUANTITY_IN_100KG"
                   (note: quantity is rounded to units of 100 kg)

Official source: https://ec.europa.eu/eurostat/web/user-guides/data-browser/
              api-data-access/api-getting-started/comext-database
No API key required. Public, free data.

Basic usage:
    from eurostat_client import EurostatClient
    client = EurostatClient()
    df = client.get_imports("ES", "CN", ["9401", "9403"])
"""

from __future__ import annotations

import time
import logging
from typing import Iterable

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Dedicated endpoint for Comext datasets (DS-). The "comext/" segment is essential.
EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data"
DATASET = "ds-045409"

# Measure names as the dataset calls them
INDICATOR_VALUE = "VALUE_IN_EUROS"
INDICATOR_QTY = "QUANTITY_IN_100KG"   # Comext rounds quantity to units of 100 kg


class EurostatClient:
    """Lightweight client for the Eurostat (Comext) external-trade dataset."""

    def __init__(self, base_url: str = EUROSTAT_BASE, dataset: str = DATASET,
                 pause: float = 0.4, timeout: int = 60):
        self.base_url = base_url
        self.dataset = dataset
        self.pause = pause
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "trade-market-analysis/1.0"})

    def _fetch_one(self, reporter: str, partner: str, product: str, flow: str,
                   year: str, indicator: str) -> pd.DataFrame:
        """Download one concrete combination (one product, one year)."""
        url = f"{self.base_url}/{self.dataset}"
        params = {
            "format": "JSON",
            "lang": "EN",
            "freq": "A",              # annual data
            "reporter": reporter,
            "partner": partner,
            "product": product,
            "flow": flow,             # "1" import, "2" export
            "indicators": indicator,
            "time": year,
        }
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        return self._parse_jsonstat(payload, reporter, partner, product,
                                    flow, indicator)

    @staticmethod
    def _parse_jsonstat(payload: dict, reporter: str, partner: str, product: str,
                        flow: str, indicator: str) -> pd.DataFrame:
        """Convert a JSON-stat 2.0 response into a clean long DataFrame.

        JSON-stat stores:
          - "value": dict {flattened_position: value}
          - "dimension"/"size"/"id": the dimension structure needed to decode
            each flattened position back into concrete categories (here, mainly
            the year).
        This function walks every value and recovers its year from the time
        dimension, robustly.
        """
        values = payload.get("value", {})
        if not values:
            return pd.DataFrame()

        # Decode the time dimension to label each value with its year
        dims = payload.get("dimension", {})
        ids = payload.get("id", [])
        sizes = payload.get("size", [])

        # Map time index -> year label
        time_index_to_label = {}
        time_dim_pos = None
        if "time" in ids:
            time_dim_pos = ids.index("time")
            cats = dims.get("time", {}).get("category", {})
            index_map = cats.get("index", {})           # {year: position}
            time_index_to_label = {v: k for k, v in index_map.items()}

        # Multipliers to un-flatten the row-major index
        def unflatten(flat_idx: int) -> list[int]:
            coords = []
            for dim_size in reversed(sizes):
                coords.append(flat_idx % dim_size)
                flat_idx //= dim_size
            return list(reversed(coords))

        rows = []
        for flat_str, val in values.items():
            flat_idx = int(flat_str)
            year_label = None
            if time_dim_pos is not None and sizes:
                coords = unflatten(flat_idx)
                time_pos = coords[time_dim_pos]
                year_label = time_index_to_label.get(time_pos)
            rows.append({
                "reporter": reporter,
                "partner": partner,
                "product": product,
                "flow": "import" if flow == "1" else "export",
                "year": int(year_label) if year_label else None,
                "indicator": indicator,
                "value": val,
            })
        return pd.DataFrame(rows)

    def _get(self, reporter: str, partner: str, products: Iterable[str],
             years: Iterable[str], flow: str, indicator: str) -> pd.DataFrame:
        frames = []
        for product in products:
            for year in years:
                try:
                    df = self._fetch_one(reporter, partner, product, flow, year, indicator)
                    if not df.empty:
                        frames.append(df)
                        logger.info("OK  %s %s %s<-%s %s: %s",
                                    "imp" if flow == "1" else "exp", product,
                                    reporter, partner, year, df["value"].iloc[0])
                    else:
                        logger.warning("empty %s %s %s", product, year, indicator)
                except requests.HTTPError as e:
                    code = e.response.status_code if e.response is not None else "?"
                    logger.error("HTTP %s for %s %s (%s)", code, product, year, indicator)
                except Exception as e:  # noqa: BLE001
                    logger.error("error %s for %s %s", e, product, year)
                time.sleep(self.pause)
        cols = ["reporter", "partner", "product", "flow", "year", "indicator", "value"]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=cols)

    def get_imports(self, reporter: str, partner: str, products: Iterable[str],
                    years: Iterable[str] | None = None,
                    indicator: str = INDICATOR_VALUE) -> pd.DataFrame:
        """Download imports (flow=1) for a list of HS products and years."""
        years = list(years) if years else ["2022", "2023", "2024"]
        return self._get(reporter, partner, list(products), years, "1", indicator)

    def get_exports(self, reporter: str, partner: str, products: Iterable[str],
                    years: Iterable[str] | None = None,
                    indicator: str = INDICATOR_VALUE) -> pd.DataFrame:
        """Download exports (flow=2) for a list of HS products and years."""
        years = list(years) if years else ["2022", "2023", "2024"]
        return self._get(reporter, partner, list(products), years, "2", indicator)


if __name__ == "__main__":
    # Quick smoke test (requires connectivity to ec.europa.eu)
    client = EurostatClient()
    demo = client.get_imports("ES", "CN", ["9401", "9403"], ["2023", "2024"])
    print(demo.to_string(index=False))
