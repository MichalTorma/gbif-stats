#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Optional

import requests


GBIF_API_BASE = "https://api.gbif.org/v1"


def fetch_org_title(org_key: str, cache: Dict[str, Optional[str]], timeout_s: int = 20) -> Optional[str]:
    if org_key in cache:
        return cache[org_key]
    url = f"{GBIF_API_BASE}/organization/{org_key}"
    try:
        resp = requests.get(url, timeout=timeout_s)
        if resp.status_code != 200:
            cache[org_key] = None
            return None
        data = resp.json()
        title = data.get("title") or data.get("name")
        cache[org_key] = title
        return title
    except Exception:
        cache[org_key] = None
        return None


def enrich_csv(input_csv: Path, output_csv: Path, timeout_s: int = 20) -> None:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    with input_csv.open("r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        # print(fieldnames)
        # Required column
        key_col = "hostingorganizationkey"
        if key_col not in fieldnames:
            raise ValueError(f"Column '{key_col}' not found in {input_csv}")

        # Add enrichment columns (append if not present)
        add_cols = ["publisherName", "publisherUrl"]
        for c in add_cols:
            if c not in fieldnames:
                fieldnames.append(c)

        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            cache: Dict[str, Optional[str]] = {}
            for row in reader:
                org_key = (row.get(key_col) or "").strip()
                if org_key:
                    title = fetch_org_title(org_key, cache=cache, timeout_s=timeout_s)
                    row["publisherName"] = title or ""
                    row["publisherUrl"] = f"https://www.gbif.org/publisher/{org_key}"
                else:
                    row["publisherName"] = ""
                    row["publisherUrl"] = ""
                writer.writerow(row)


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Enrich GBIF SQL results with publisher name and link via Registry API")
    p.add_argument("input_csv", type=Path, help="Path to CSV produced by the SQL download")
    p.add_argument("output_csv", type=Path, help="Where to write the enriched CSV")
    p.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds (default: 20)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        enrich_csv(args.input_csv, args.output_csv, timeout_s=args.timeout)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


