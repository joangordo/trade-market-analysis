"""
test_scoring.py
===============
Unit tests for the scoring logic. Run with:
    cd trade-market-analysis && python -m pytest tests/ -v

No connectivity required: they validate the engine's maths with controlled data.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_scoring import (  # noqa: E402
    build_features, score_markets, ScoringWeights, _cagr, _minmax,
)


def test_cagr_basic():
    # Doubling in 2 years -> ~41.4% CAGR
    assert _cagr(100, 200, 2) == pytest.approx(0.41421, abs=1e-4)


def test_cagr_handles_zero_and_negative():
    assert _cagr(0, 100, 2) == 0.0
    assert _cagr(100, 0, 2) == 0.0
    assert _cagr(100, 200, 0) == 0.0


def test_minmax_constant_series_returns_neutral():
    s = pd.Series([5, 5, 5])
    assert (_minmax(s) == 0.5).all()


def test_minmax_range():
    s = pd.Series([0, 5, 10])
    out = _minmax(s)
    assert out.min() == 0.0 and out.max() == 1.0


def test_build_features_computes_growth():
    df = pd.DataFrame({
        "product": ["A"] * 3, "year": [2022, 2023, 2024],
        "value": [100, 150, 225],  # +50% a year
    })
    feats = build_features(df)
    assert len(feats) == 1
    assert feats["cagr"].iloc[0] == pytest.approx(0.5, abs=1e-6)


def test_build_features_skips_single_year():
    df = pd.DataFrame({"product": ["A"], "year": [2024], "value": [100]})
    assert build_features(df).empty


def test_score_orders_higher_growth_first():
    df = pd.DataFrame({
        "product": ["fast", "fast", "fast", "slow", "slow", "slow"],
        "year": [2022, 2023, 2024, 2022, 2023, 2024],
        "value": [100, 200, 400, 100, 102, 104],
    })
    feats = build_features(df)
    w = ScoringWeights(growth=1, size=0, momentum=0, price=0)
    scored = score_markets(feats, w)
    assert scored.iloc[0]["product"] == "fast"


def test_weights_normalise():
    w = ScoringWeights(growth=2, size=2, momentum=2, price=2).normalised()
    assert (w.growth + w.size + w.momentum + w.price) == pytest.approx(1.0)


def test_score_in_valid_range():
    df = pd.DataFrame({
        "product": ["A", "A", "B", "B", "C", "C"],
        "year": [2023, 2024, 2023, 2024, 2023, 2024],
        "value": [100, 120, 500, 480, 50, 90],
    })
    feats = build_features(df)
    scored = score_markets(feats)
    assert scored["score"].between(0, 100).all()


def test_empty_input_returns_empty():
    empty = pd.DataFrame(columns=["product", "year", "value"])
    feats = build_features(empty)
    assert feats.empty
    assert score_markets(feats).empty


def test_missing_price_does_not_break_scoring():
    """Real-world case: value present, quantity entirely missing."""
    df = pd.DataFrame({
        "product": ["A", "A", "B", "B"], "year": [2023, 2024, 2023, 2024],
        "value": [100, 150, 500, 600],
    })
    feats = build_features(df, quantity_df=pd.DataFrame(columns=["product", "year", "value"]))
    assert feats["unit_price"].isna().all()
    scored = score_markets(feats)
    assert scored["score"].between(0, 100).all()
