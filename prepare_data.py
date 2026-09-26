"""
Prepare Pakistan carbon-emission data for the dashboard.

Reads the Our World in Data CO2 dataset (owid-co2-data.csv) and writes a small
data.json containing only the four views the dashboard needs. Keeping the
aggregation in Python and shipping a compact JSON means the page loads in
kilobytes instead of parsing a 14 MB CSV in the browser.

Usage:
    python prepare_data.py

Data source: Our World in Data, "CO2 and Greenhouse Gas Emissions"
https://github.com/owid/co2-data  (Global Carbon Budget, licensed CC BY)
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

CSV_PATH = Path("owid-co2-data.csv")
OUT_PATH = Path("data.json")

COUNTRY = "Pakistan"
PEERS = ["Pakistan", "India", "Bangladesh", "Iran"]

TREND_START = 1960       # start of the long-run trend chart
SOURCE_START = 1990      # fuel-source breakdown: recent decades only
DECOUPLING_START = 1990  # GDP is only reported for part of the series

# The five fuel/process sources that sum to the national total in this dataset.
SOURCE_COLUMNS = {
    "coal": "coal_co2",
    "oil": "oil_co2",
    "gas": "gas_co2",
    "cement": "cement_co2",
    "flaring": "flaring_co2",
}


# ----------------------------------------------------------------------------
# Load
# ----------------------------------------------------------------------------

def load() -> pd.DataFrame:
    """Read the full OWID file and keep only the columns we actually use."""
    columns = [
        "country", "year", "iso_code", "population", "gdp",
        "co2", "co2_per_capita", "share_global_co2",
        *SOURCE_COLUMNS.values(),
    ]
    df = pd.read_csv(CSV_PATH, usecols=columns)

    # OWID mixes real countries with aggregates like "World", "Asia" and
    # "High-income countries". Aggregates have no ISO code, so we can separate
    # them cleanly instead of maintaining a blocklist of names.
    df["is_country"] = df["iso_code"].notna() & (df["iso_code"].str.len() == 3)
    return df


# ----------------------------------------------------------------------------
# The four views
# ----------------------------------------------------------------------------

def headline(df: pd.DataFrame) -> dict:
    """Latest-year summary figures shown at the top of the page."""
    pk = df[df["country"] == COUNTRY].dropna(subset=["co2"])
    latest = pk.loc[pk["year"].idxmax()]
    year = int(latest["year"])

    world = df[(df["country"] == "World") & (df["year"] == year)].iloc[0]

    # How Pakistan ranks on per-capita emissions among countries with data
    # that year: 1 = highest emitter per person.
    peers_that_year = df[
        df["is_country"]
        & (df["year"] == year)
        & df["co2_per_capita"].notna()
    ]
    rank = int((peers_that_year["co2_per_capita"] > latest["co2_per_capita"]).sum()) + 1

    return {
        "year": year,
        "co2_total_mt": round(float(latest["co2"]), 1),
        "co2_per_capita_t": round(float(latest["co2_per_capita"]), 3),
        "world_per_capita_t": round(float(world["co2_per_capita"]), 2),
        "share_global_pct": round(float(latest["share_global_co2"]), 3),
        "population_m": round(float(latest["population"]) / 1e6, 1),
        "per_capita_rank": rank,
        "countries_ranked": int(len(peers_that_year)),
    }


def trend(df: pd.DataFrame) -> dict:
    """Chart 1 — national total against emissions per person, same time axis."""
    pk = df[(df["country"] == COUNTRY) & (df["year"] >= TREND_START)]
    pk = pk.dropna(subset=["co2"]).sort_values("year")
    return {
        "years": pk["year"].astype(int).tolist(),
        "total_mt": pk["co2"].round(2).tolist(),
        "per_capita_t": pk["co2_per_capita"].round(3).tolist(),
    }


def peers(df: pd.DataFrame) -> dict:
    """Chart 2 — per-capita emissions for Pakistan and three regional neighbours."""
    sub = df[df["country"].isin(PEERS) & (df["year"] >= TREND_START)]
    sub = sub.dropna(subset=["co2_per_capita"])

    # Pivot to one column per country so every series shares one year axis.
    wide = sub.pivot(index="year", columns="country", values="co2_per_capita")
    wide = wide.sort_index().round(3)

    return {
        "years": wide.index.astype(int).tolist(),
        # None (not NaN) so the values stay valid JSON; Chart.js draws a gap.
        "series": {c: [None if pd.isna(v) else v for v in wide[c]] for c in PEERS},
    }


def sources(df: pd.DataFrame) -> dict:
    """Chart 3 — which fuels and processes the national total is made of."""
    pk = df[(df["country"] == COUNTRY) & (df["year"] >= SOURCE_START)].sort_values("year")
    pk = pk.dropna(subset=["co2"])

    out = {"years": pk["year"].astype(int).tolist()}
    for label, column in SOURCE_COLUMNS.items():
        out[label] = pk[column].fillna(0).round(2).tolist()

    # Sanity check: the parts should reconstruct the published national total.
    reconstructed = pk[list(SOURCE_COLUMNS.values())].fillna(0).sum(axis=1)
    largest_gap = float((reconstructed - pk["co2"]).abs().max())
    out["max_reconstruction_gap_mt"] = round(largest_gap, 3)

    return out


def decoupling(df: pd.DataFrame) -> list:
    """Chart 4 — does economic growth still pull emissions up with it?

    Each point is one year, positioned by GDP per person (x) and CO2 per
    person (y). Drawn as a connected path, it shows whether the country is
    moving right and up together, or starting to bend.
    """
    pk = df[(df["country"] == COUNTRY) & (df["year"] >= DECOUPLING_START)]
    pk = pk.dropna(subset=["gdp", "population", "co2_per_capita"]).sort_values("year")

    return [
        {
            "year": int(row.year),
            "gdp_per_capita": round(row.gdp / row.population, 1),
            "co2_per_capita": round(row.co2_per_capita, 3),
        }
        for row in pk.itertuples()
    ]


# ----------------------------------------------------------------------------
# Write
# ----------------------------------------------------------------------------

def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(
            f"{CSV_PATH} not found. Download it first:\n"
            "  curl -L -o owid-co2-data.csv "
            "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
        )

    df = load()

    payload = {
        "meta": {
            "country": COUNTRY,
            "source": "Our World in Data — CO2 and Greenhouse Gas Emissions "
                      "(Global Carbon Budget)",
            "source_url": "https://github.com/owid/co2-data",
            "prepared_on": date.today().isoformat(),
            "units": {
                "total": "million tonnes CO2",
                "per_capita": "tonnes CO2 per person",
                "gdp_per_capita": "international-$ (2011 prices)",
            },
        },
        "headline": headline(df),
        "trend": trend(df),
        "peers": peers(df),
        "sources": sources(df),
        "decoupling": decoupling(df),
    }

    OUT_PATH.write_text(json.dumps(payload, indent=1))

    h = payload["headline"]
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)")
    print(f"Latest year: {h['year']}")
    print(f"  total          {h['co2_total_mt']} Mt CO2")
    print(f"  per capita     {h['co2_per_capita_t']} t "
          f"(world {h['world_per_capita_t']} t)")
    print(f"  global share   {h['share_global_pct']}%")
    print(f"  per-capita rank {h['per_capita_rank']} of {h['countries_ranked']}")
    print(f"Source breakdown reconstructs the total to within "
          f"{payload['sources']['max_reconstruction_gap_mt']} Mt")


if __name__ == "__main__":
    main()
