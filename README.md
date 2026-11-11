# 📊 Trade Market Analysis — Import Opportunity Scoring (Spain ← China)

> Data-driven selection of product categories to import from China into Spain,
> using official EU trade statistics and a transparent, configurable
> market-scoring model.

This project answers a real business question: **which product categories are
worth importing from China into Spain?** Instead of deciding by intuition, it
pulls official EU external-trade data, engineers objective indicators per
sector, and scores each one for market attractiveness.

It covers the full data-science cycle end to end — **API ingestion → cleaning →
feature engineering → configurable scoring → visualisation → tests** — and is
built around a genuine decision I was researching, not a toy dataset.

---

## 🎯 The problem

An importer must choose a sector before committing capital to stock, logistics
and factory relationships. Choosing wrong is expensive. This project treats
sector selection as a data problem: it surfaces categories with **growing
demand**, **sufficient market size**, **recent acceleration** and **high unit
price** (a proxy for value-added and margin, rather than bulk commodity).

## 🧠 Methodology

For each product category (4-digit HS code) four signals are computed, all
normalised to [0, 1]:

| Signal | What it measures | Why it matters |
|---|---|---|
| **Growth** | CAGR of imported value | Structural demand trend |
| **Size** | Absolute imported value (log) | Market big enough to operate in |
| **Momentum** | Latest year vs historical mean | Recent acceleration |
| **Price** | Unit price (value / quantity) | Value-added and margin potential |

The final score is a **configurable weighted mean**:

```
score = w_growth·growth + w_size·size + w_momentum·momentum + w_price·price
```

Default weights (0.35 / 0.20 / 0.25 / 0.20) prioritise growth and momentum, but
can be tuned to any strategy.

## 📈 Real findings (Spain ← China, 2020–2024)

Run against live Eurostat data, the model surfaced some non-obvious insights:

- **Bicycles ranked #1 on raw score but are a false positive** — a ~€1M market
  whose high CAGR is statistical noise on a tiny base. A key lesson the project
  makes explicit: *human judgement sits on top of the score, not under it.*
- **Leather goods / bags (HS 4202)** stand out: a large market (~€758M) with
  healthy growth and a high unit price — strong margin and light logistics.
- **Tableware & glassware (HS 6911/7013)** are high-growth niche markets
  (+18–19% CAGR) suited to a value/specialisation play rather than volume.
- **Furniture (sofas, HS 9401)** is a large, solid market (~€559M) but with a
  low unit price — heavy, bulky goods where freight erodes margin.

> The point isn't the ranking itself — it's that the model turns a vague
> question ("what should I import?") into an evidence-based shortlist to
> investigate, and flags where naïve metrics mislead.

## 📁 Project structure

```
trade-market-analysis/
├── src/
│   ├── eurostat_client.py     # Eurostat Comext API client (real data)
│   ├── product_catalogue.py   # Universe of HS categories to analyse
│   ├── market_scoring.py      # Feature engineering + scoring (analytical core)
│   ├── synthetic_data.py      # Demo data generator (offline runs)
│   ├── diagnose_api.py        # Single-call API connectivity check
│   └── run_analysis.py        # Main pipeline + visualisations
├── tests/
│   └── test_scoring.py        # Unit tests for the scoring logic
├── notebooks/
│   └── market_analysis.ipynb  # Step-by-step explained analysis
├── outputs/                   # Charts and result CSVs
├── requirements.txt
└── README.md
```

## 🚀 How to run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Offline demo (synthetic data, no connection)
cd src
python run_analysis.py --source synthetic

# 3. (Recommended) Verify API connectivity with a single call
python diagnose_api.py

# 4. Real Eurostat data
python run_analysis.py --source eurostat --reporter ES --partner CN
```

Results are written to `outputs/`:
- `market_scores.csv` — full scored, ranked table.
- `top_scores.png` — ranking of the most attractive categories.
- `opportunity_map.png` — growth vs size map (the key strategic chart).

## 🛠️ Engineering notes (things that went wrong, and how they were handled)

Real data is messy. Two bugs worth highlighting, because solving them is the
difference between a demo and something that works:

1. **Wrong endpoint.** `DS-`-prefixed datasets live on Eurostat's **Comext**
   endpoint (`.../api/comext/dissemination/...`), not the general one — every
   call returned 404 until this was fixed.
2. **Silent empty quantity.** The quantity measure is `QUANTITY_IN_100KG`
   (not `_IN_KG`), and Comext rounds to 100-kg units. The wrong name returned
   empty results for every row, which then crashed the price-sized scatter plot.
   The pipeline now degrades gracefully: if price data is missing, the scoring
   stays valid (three signals) and the chart falls back to uniform point size.

Both are covered by the test suite and documented in the API client.

## 🔍 Data sources

- **Eurostat — International trade in goods** (dataset `DS-045409`): official EU
  data by HS code, no API key, free.
- Extensions: UN Comtrade, Datacomex (Spain, province-level detail),
  ITC Trade Map.

## 🧪 Tests

```bash
python -m pytest tests/ -v
```

The scoring logic is covered by unit tests (CAGR, normalisation, ranking,
and edge cases: zeros, empty series, fully missing price data).

## 🛣️ Possible extensions

- Company-level data (bills of lading) to identify existing competitors.
- Spanish retail prices to estimate real margin per sector.
- Confidence intervals on trends (bootstrap) to quantify uncertainty.
- Province-level detail via Datacomex (e.g. what enters through Catalonia).

## 📄 License

MIT — free to use, modify and distribute.

---

*Built as both a market-analysis tool and a data-science portfolio project
applied to international trade.*
