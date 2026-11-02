"""Download daily onion, tomato and potato prices from data.gov.in.

Source: "Variety-wise Daily Market Prices Data of Commodity", published by the
Directorate of Marketing and Inspection from Agmarknet, under the Open Government
License India. It holds prices only, with no arrival quantities.

The steps run slowly on purpose and can be restarted: each finished file is recorded
in data/raw/manifest.json and skipped next time.

Needs DATA_GOV_IN_API_KEY in a .env file in the project root (never commit it).

Run from the project root:
  python -m src.collect --rank     # choose the busiest districts for each crop
  python -m src.collect            # download their full histories
"""
import argparse
import gzip
import json
import re
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw")
DISTRICTS = RAW / "districts.json"
MANIFEST = RAW / "manifest.json"
URL = "https://www.data.gov.in/backend/dataapi/v1/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

CROPS = ["Onion", "Tomato", "Potato"]
RANK_YEAR = 2024
TOP_DISTRICTS = 20
MIN_DAYS_REPORTED = 250  # a district must report on most days of the ranking year
PAGE_SIZE = 5000  # as quick to serve as 1,000, while 10,000 takes five times longer
PAUSE_SECONDS = 1.0
RETRIES = 6
TIMEOUT = 90
# Districts renamed or split at the source. Later rows sit under the new name.
NEW_DISTRICT_NAMES = {"Ahmednagar": "Ahilyanagar", "Kolar": "Chikkaballapur", "Chittor": "Annamayya"}


def api_key():
    match = re.search(r"DATA_GOV_IN_API_KEY\s*=\s*(\S+)", Path(".env").read_text(encoding="utf-8-sig"))
    if not match:
        raise SystemExit("Add DATA_GOV_IN_API_KEY to a .env file in the project root.")
    return match.group(1).strip("\"'")


def get_page(key, filters, offset):
    """One page of results. The key is never printed, even when a request fails."""
    params = {"api-key": key, "format": "json", "limit": PAGE_SIZE, "offset": offset, **filters}
    for attempt in range(RETRIES):
        try:
            response = requests.get(URL, params=params, headers=HEADERS, timeout=TIMEOUT)
            body = response.json() if response.ok else {}
            if "records" in body:
                time.sleep(PAUSE_SECONDS)
                return body
            problem = f"HTTP {response.status_code}, {str(body.get('message', 'no records')).replace(key, '***')[:80]}"
        except (requests.RequestException, ValueError) as error:
            problem = type(error).__name__
        wait = 5 * 2 ** attempt
        print(f"  {problem} at offset {offset}, retrying in {wait}s", flush=True)
        time.sleep(wait)
    raise SystemExit(f"Giving up at offset {offset} after {RETRIES} tries. Run again to resume.")


def fetch_all(key, filters):
    """Every record for these filters, with the total the server reported."""
    first = get_page(key, filters, 0)
    total = int(first["total"])
    records = list(first["records"])
    while len(records) < total:
        page = get_page(key, filters, len(records))["records"]
        if not page:
            break
        records.extend(page)
    return records, total


def rank_districts(key):
    """Pick the districts with the most records among those reporting nearly every day."""
    chosen = json.loads(DISTRICTS.read_text(encoding="utf-8"))["districts"] if DISTRICTS.exists() else {}
    for crop in CROPS:
        if crop in chosen:
            continue
        filters = {"filters[Commodity]": crop, "range[Arrival_Date][gte]": f"{RANK_YEAR}-01-01",
                   "range[Arrival_Date][lte]": f"{RANK_YEAR}-12-31"}
        records, total = fetch_all(key, filters)
        frame = pd.DataFrame(records)
        summary = frame.groupby(["State", "District"]).agg(
            rows=("Arrival_Date", "size"), days=("Arrival_Date", "nunique"), markets=("Market", "nunique")).reset_index()
        steady = summary[summary["days"] >= MIN_DAYS_REPORTED].nlargest(TOP_DISTRICTS, "rows")
        chosen[crop] = steady.to_dict("records")
        print(f"{crop}: {len(frame):,} of {total:,} rows in {RANK_YEAR}, {len(steady)} districts chosen", flush=True)
        print(steady.head(5).to_string(index=False), flush=True)
        DISTRICTS.write_text(json.dumps({"rank_year": RANK_YEAR, "districts": chosen}, indent=2), encoding="utf-8")


def file_for(crop, state, district):
    name = re.sub(r"[^A-Za-z0-9]+", "_", f"{state}__{district}").strip("_")
    return RAW / crop.lower() / f"{name}.csv.gz"


def download(key):
    if not DISTRICTS.exists():
        raise SystemExit("Run python -m src.collect --rank first.")
    chosen = json.loads(DISTRICTS.read_text(encoding="utf-8"))["districts"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    for crop, districts in chosen.items():
        renamed = [{**row, "District": NEW_DISTRICT_NAMES[row["District"]]} for row in districts
                   if row["District"] in NEW_DISTRICT_NAMES]
        for row in districts + renamed:
            path = file_for(crop, row["State"], row["District"])
            if path.as_posix() in manifest and path.exists():
                continue
            filters = {"filters[Commodity]": crop, "filters[State]": row["State"], "filters[District]": row["District"]}
            records, total = fetch_all(key, filters)
            path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
                pd.DataFrame(records).to_csv(handle, index=False)
            manifest[path.as_posix()] = {"rows": len(records), "server_total": total, "downloaded": date.today().isoformat()}
            MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            print(f"{crop} {row['District']}: {len(records):,} of {total:,}", flush=True)
    print(f"done: {len(manifest)} files, {sum(m['rows'] for m in manifest.values()):,} rows", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rank", action="store_true", help="choose districts instead of downloading")
    arguments = parser.parse_args()
    key = api_key()
    rank_districts(key) if arguments.rank else download(key)


if __name__ == "__main__":
    main()
