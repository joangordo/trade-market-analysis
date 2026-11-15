"""
diagnose_api.py
===============
Diagnostic tool: makes ONE call to the Eurostat API and prints the raw
response, so you can verify connectivity and structure before launching the
full pipeline.

Usage:
    cd src
    python diagnose_api.py

If it works, you'll see real sofa (HS 9401) import data ES<-CN.
If it fails, you'll see the HTTP error code and response body, which help
adjust the parameters.
"""

from __future__ import annotations

import json
import requests

BASE = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data"
DATASET = "ds-045409"


def diagnose():
    url = f"{BASE}/{DATASET}"
    params = {
        "format": "JSON", "lang": "EN", "freq": "A",
        "reporter": "ES", "partner": "CN", "product": "9401",
        "flow": "1", "indicators": "VALUE_IN_EUROS", "time": "2023",
    }
    print("Request URL:")
    print(requests.Request("GET", url, params=params).prepare().url)
    print("-" * 70)

    try:
        r = requests.get(url, params=params, timeout=60)
    except Exception as e:  # noqa: BLE001
        print(f"Connection ERROR: {e}")
        return

    print(f"HTTP status code: {r.status_code}")
    print("-" * 70)

    if r.status_code != 200:
        print("Response body (first 1500 chars):")
        print(r.text[:1500])
        print("\nHINTS by code:")
        print("  404 -> wrong endpoint or non-existent dataset")
        print("  400 -> a parameter is misspelled (check dimension names)")
        print("  413 -> query too large (a filter is missing)")
        print("  416 -> no data for that year/product combination")
        return

    try:
        data = r.json()
    except Exception as e:  # noqa: BLE001
        print(f"Response is not valid JSON: {e}")
        print(r.text[:800])
        return

    print("JSON received correctly. Main keys:")
    print(" ", list(data.keys()))
    print("\nDimensions (id):", data.get("id"))
    print("Sizes (size):   ", data.get("size"))
    values = data.get("value", {})
    print(f"\nNumber of values: {len(values)}")
    if values:
        print("Values:", json.dumps(values, indent=2)[:500])
        print("\nOK CONNECTION WORKS. You can now run:")
        print("  python run_analysis.py --source eurostat --reporter ES --partner CN")
    else:
        print("Response with no values: maybe no data for this combination.")


if __name__ == "__main__":
    diagnose()
