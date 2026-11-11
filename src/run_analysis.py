"""
run_analysis.py
===============
Main market-analysis pipeline for ES<-CN imports.

Orchestrates the whole flow:
    1. Load data (real Eurostat OR synthetic, per --source).
    2. Build per-category features.
    3. Score and rank the markets.
    4. Generate visualisations and save results to outputs/.

Usage:
    python run_analysis.py --source synthetic          # offline demo
    python run_analysis.py --source eurostat            # real data
    python run_analysis.py --source eurostat --partner CN --reporter ES
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from product_catalogue import get_valid_hs_codes, label_for, group_for
from market_scoring import build_features, score_markets, ScoringWeights
from synthetic_data import generate_trade_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

sns.set_theme(style="whitegrid", palette="deep")


def load_data(source: str, reporter: str, partner: str, years: list[int]):
    """Load value and quantity data from the chosen source."""
    if source == "synthetic":
        logger.info("Generating synthetic data (offline demo)")
        return generate_trade_data(years=years)

    if source == "eurostat":
        from eurostat_client import EurostatClient, INDICATOR_VALUE, INDICATOR_QTY
        client = EurostatClient()
        codes = get_valid_hs_codes()
        year_strs = [str(y) for y in years]
        logger.info("Downloading value from Eurostat (%d products)...", len(codes))
        value_df = client.get_imports(reporter, partner, codes, year_strs, INDICATOR_VALUE)
        logger.info("Downloading quantity from Eurostat...")
        qty_df = client.get_imports(reporter, partner, codes, year_strs, INDICATOR_QTY)
        return value_df, qty_df

    raise ValueError(f"Unknown source: {source}")


def enrich(scored: pd.DataFrame) -> pd.DataFrame:
    """Add readable labels and thematic group."""
    scored = scored.copy()
    scored["label"] = scored["product"].map(label_for)
    scored["group"] = scored["product"].map(group_for)
    front = ["product", "label", "group", "score", "cagr", "momentum",
             "unit_price", "value_latest"]
    rest = [c for c in scored.columns if c not in front]
    return scored[[c for c in front if c in scored.columns] + rest]


def plot_top_scores(scored: pd.DataFrame, top_n: int = 12) -> Path:
    """Horizontal bar chart of the most attractive categories."""
    top = scored.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = sns.color_palette("viridis", len(top))
    ax.barh(top["label"], top["score"], color=colors)
    ax.set_xlabel("Market attractiveness score (0-100)")
    ax.set_title(f"Top {top_n} ES\u2190CN import categories by attractiveness",
                 fontsize=13, weight="bold")
    for i, (_, row) in enumerate(top.iterrows()):
        ax.text(row["score"] + 0.5, i, f"{row['score']:.0f}", va="center", fontsize=9)
    plt.tight_layout()
    path = OUTPUT_DIR / "top_scores.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_growth_vs_size(scored: pd.DataFrame) -> Path:
    """Growth vs size scatter, colour by group, point size by unit price.

    The most strategic chart: identifies categories in the
    'high growth + large enough market' quadrant.
    Robust to a fully missing unit_price column (falls back to fixed size).
    """
    fig, ax = plt.subplots(figsize=(11, 7))
    groups = scored["group"].unique()
    palette = dict(zip(groups, sns.color_palette("tab20", len(groups))))

    global_price_median = scored["unit_price"].median()
    has_price = pd.notna(global_price_median)

    for group in groups:
        sub = scored[scored["group"] == group]
        if has_price:
            filled = sub["unit_price"].fillna(global_price_median)
            sizes = (filled * 8).clip(30, 400)
        else:
            sizes = 90  # uniform size when no price data
        ax.scatter(sub["value_latest"] / 1e6, sub["cagr"] * 100,
                   s=sizes, alpha=0.7, label=group,
                   color=palette[group], edgecolors="white", linewidth=0.5)

    ax.axhline(scored["cagr"].median() * 100, ls="--", color="grey", alpha=0.6)
    ax.axvline((scored["value_latest"] / 1e6).median(), ls="--", color="grey", alpha=0.6)

    for _, row in scored.head(6).iterrows():
        ax.annotate(row["label"], (row["value_latest"] / 1e6, row["cagr"] * 100),
                    fontsize=8, xytext=(5, 5), textcoords="offset points")

    price_note = ("point size = unit price \u2248 value added"
                  if has_price else "uniform size (no price data)")
    ax.set_xscale("log")
    ax.set_xlabel("Market size: imported value latest year (EUR millions, log scale)")
    ax.set_ylabel("Demand growth (CAGR %)")
    ax.set_title("Opportunity map: growth vs market size\n"
                 f"({price_note})", fontsize=13, weight="bold")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8, title="Sector")
    plt.tight_layout()
    path = OUTPUT_DIR / "opportunity_map.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description="ES<-CN import market analysis")
    parser.add_argument("--source", choices=["synthetic", "eurostat"],
                        default="synthetic", help="Data source")
    parser.add_argument("--reporter", default="ES", help="Declaring country (ISO)")
    parser.add_argument("--partner", default="CN", help="Partner country (ISO)")
    parser.add_argument("--years", default="2020,2021,2022,2023,2024",
                        help="Comma-separated years")
    args = parser.parse_args()

    years = [int(y) for y in args.years.split(",")]
    OUTPUT_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    value_df, qty_df = load_data(args.source, args.reporter, args.partner, years)
    if value_df.empty:
        logger.error("No data. Check connectivity or parameters.")
        return
    value_df.to_csv(DATA_DIR / "raw_value.csv", index=False)
    qty_df.to_csv(DATA_DIR / "raw_quantity.csv", index=False)

    features = build_features(value_df, qty_df)
    scored = enrich(score_markets(features, ScoringWeights()))
    scored.to_csv(OUTPUT_DIR / "market_scores.csv", index=False)

    p1 = plot_top_scores(scored)
    p2 = plot_growth_vs_size(scored)

    logger.info("Analysis complete. Top 5 categories:")
    cols = ["label", "group", "score", "cagr", "value_latest"]
    print("\n" + scored[cols].head(5).to_string(index=False))
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print(f"  - market_scores.csv\n  - {p1.name}\n  - {p2.name}")


if __name__ == "__main__":
    main()
