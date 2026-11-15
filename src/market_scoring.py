"""
market_scoring.py
=================
Analytical engine that turns raw trade data into a market-attractiveness score
for each product category.

The idea: don't pick an import sector by intuition — score each category on
objective signals and let the data rank the opportunities. Weights are
configurable so each strategy can be expressed.

Signals combined (all normalised to 0-1):
    1. GROWTH   - demand growth (CAGR of imported value).
    2. SIZE     - market size (absolute imported value, log scale).
    3. MOMENTUM - recent acceleration (latest year vs historical mean).
    4. PRICE    - value-added signal (unit price = value / quantity);
                  a high unit price suggests margin, not bulk commodity.

Final score = weighted mean of the signals. Weights configurable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ScoringWeights:
    """Weight of each signal. Should sum to 1.0 (normalised if not)."""
    growth: float = 0.35
    size: float = 0.20
    momentum: float = 0.25
    price: float = 0.20

    def normalised(self) -> "ScoringWeights":
        total = self.growth + self.size + self.momentum + self.price
        if total == 0:
            raise ValueError("Weights cannot sum to zero")
        return ScoringWeights(
            growth=self.growth / total,
            size=self.size / total,
            momentum=self.momentum / total,
            price=self.price / total,
        )


def _minmax(series: pd.Series) -> pd.Series:
    """Min-max normalisation, robust to constant or NaN series."""
    s = series.astype(float)
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.5, index=s.index)  # no variation -> neutral
    return (s - lo) / (hi - lo)


def _cagr(first: float, last: float, periods: int) -> float:
    """Compound annual growth rate. Robust to zeros/negatives."""
    if periods <= 0 or first <= 0 or last <= 0:
        return 0.0
    return (last / first) ** (1.0 / periods) - 1.0


def build_features(value_df: pd.DataFrame,
                   quantity_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build the per-product feature table from long-format data.

    Args:
        value_df: long DataFrame with columns [product, year, value] (EUR value).
        quantity_df: optional, same format but with weight/quantity, to compute
                     the unit price.

    Returns:
        DataFrame with one row per product and the raw (un-normalised) features.
    """
    rows = []
    for product, grp in value_df.groupby("product"):
        grp = grp.sort_values("year")
        years = grp["year"].tolist()
        vals = grp["value"].tolist()
        if len(vals) < 2:
            continue

        first_val, last_val = vals[0], vals[-1]
        n_periods = years[-1] - years[0]
        cagr = _cagr(first_val, last_val, n_periods)

        # Momentum: latest year vs mean of previous years
        if len(vals) >= 3:
            prior_mean = np.mean(vals[:-1])
            momentum = (last_val - prior_mean) / prior_mean if prior_mean > 0 else 0.0
        else:
            momentum = cagr

        # Mean unit price (if we have quantities).
        # Note: Comext reports quantity in units of 100 kg, so value/quantity
        # = EUR/100kg. Divide by 100 to get EUR/kg.
        unit_price = np.nan
        if quantity_df is not None:
            q = quantity_df[quantity_df["product"] == product].sort_values("year")
            if not q.empty:
                merged = grp.merge(q, on="year", suffixes=("_val", "_qty"))
                merged = merged[merged["value_qty"] > 0]
                if not merged.empty:
                    unit_price = (merged["value_val"] / merged["value_qty"]).mean() / 100.0

        rows.append({
            "product": product,
            "value_latest": last_val,
            "cagr": cagr,
            "momentum": momentum,
            "unit_price": unit_price,
            "years_covered": f"{years[0]}-{years[-1]}",
        })

    return pd.DataFrame(rows)


def score_markets(features: pd.DataFrame,
                  weights: ScoringWeights | None = None) -> pd.DataFrame:
    """Score each product by combining the normalised signals.

    Returns:
        DataFrame sorted by descending score, with normalised signal columns
        and the final score (0-100).
    """
    if features.empty:
        return features
    w = (weights or ScoringWeights()).normalised()

    df = features.copy()
    df["growth_n"] = _minmax(df["cagr"])
    df["size_n"] = _minmax(np.log1p(df["value_latest"].clip(lower=0)))
    df["momentum_n"] = _minmax(df["momentum"])
    # Price can be NaN; fill with the median before normalising
    price_filled = df["unit_price"].fillna(df["unit_price"].median())
    df["price_n"] = _minmax(price_filled)

    df["score"] = (
        w.growth * df["growth_n"]
        + w.size * df["size_n"]
        + w.momentum * df["momentum_n"]
        + w.price * df["price_n"]
    ) * 100.0

    return df.sort_values("score", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    # Self-test with minimal data
    demo = pd.DataFrame({
        "product": ["9401", "9401", "9401", "8516", "8516", "8516"],
        "year": [2022, 2023, 2024, 2022, 2023, 2024],
        "value": [100, 130, 180, 500, 490, 495],
    })
    feats = build_features(demo)
    print(score_markets(feats)[["product", "cagr", "momentum", "score"]])
