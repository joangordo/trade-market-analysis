"""
synthetic_data.py
=================
Generator of synthetic-but-realistic trade data, so the full pipeline can run
and be tested without connectivity to the Eurostat API.

The patterns (growth, cross-category price levels) are inspired by plausible
orders of magnitude for ES<-CN imports, but are NOT real data. When you connect
the Eurostat API, this source is replaced.

A fixed seed guarantees reproducibility.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from product_catalogue import get_valid_hs_codes, group_for

# Plausible growth profiles per thematic group (approx. base CAGR)
_GROUP_GROWTH = {
    "Furniture": 0.06, "Home": 0.04, "Home textile": 0.03, "Decoration": 0.08,
    "Appliances": 0.05, "Electronics": 0.09, "Sport & leisure": 0.11,
    "Accessories": 0.07, "Footwear": 0.02, "Textile": 0.01, "Hardware": 0.05,
    "Other": 0.04,
}

# Relative unit price level per group (value-added proxy)
_GROUP_PRICE = {
    "Electronics": 45.0, "Appliances": 28.0, "Furniture": 22.0,
    "Accessories": 18.0, "Decoration": 15.0, "Sport & leisure": 20.0,
    "Home": 9.0, "Footwear": 12.0, "Home textile": 7.0, "Textile": 6.0,
    "Hardware": 11.0, "Other": 10.0,
}


def generate_trade_data(years: list[int] | None = None,
                        seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate synthetic value and quantity data for the full catalogue.

    Returns:
        (value_df, quantity_df) in long format [product, year, value].
    """
    years = years or [2020, 2021, 2022, 2023, 2024]
    rng = np.random.default_rng(seed)

    value_rows, qty_rows = [], []
    for code in get_valid_hs_codes():
        group = group_for(code)
        base_growth = _GROUP_GROWTH.get(group, 0.04)
        base_price = _GROUP_PRICE.get(group, 10.0)

        base_value = rng.uniform(5e6, 2.5e8)  # between 5M and 250M EUR
        growth = base_growth + rng.normal(0, 0.03)
        unit_price = max(2.0, base_price * rng.uniform(0.7, 1.3))

        for i, year in enumerate(years):
            shock = rng.normal(1.0, 0.05)
            value = base_value * ((1 + growth) ** i) * shock
            # quantity in 100kg units, consistent with Comext
            quantity = (value / unit_price) / 100.0 * rng.uniform(0.95, 1.05)

            value_rows.append({"reporter": "ES", "partner": "CN", "product": code,
                               "flow": "import", "year": year,
                               "indicator": "VALUE_IN_EUROS", "value": round(value, 0)})
            qty_rows.append({"reporter": "ES", "partner": "CN", "product": code,
                             "flow": "import", "year": year,
                             "indicator": "QUANTITY_IN_100KG", "value": round(quantity, 0)})

    return pd.DataFrame(value_rows), pd.DataFrame(qty_rows)


if __name__ == "__main__":
    v, q = generate_trade_data()
    print(f"Value: {len(v)} rows, Quantity: {len(q)} rows")
    print(v.head(10).to_string(index=False))
