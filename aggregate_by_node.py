#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


NUM_COLS = [
    "total_records",
    "records_with_recordedbyid",
    "records_with_valid_recordedbyid",
    "records_with_invalid_recordedbyid",
    "records_with_orcid",
    "records_with_google_scholar",
    "records_with_researcherid",
    "records_with_wikidata",
    "records_with_linkedin",
]


def read_node_org_map(path: Path) -> Dict[str, List[Tuple[str, str]]]:
    node_to_orgs: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            node_key = row.get("nodeKey") or ""
            node_title = row.get("nodeTitle") or ""
            org_key = row.get("publishingOrgKey") or ""
            org_title = row.get("publisherName") or ""
            if node_key and org_key:
                node_to_orgs[node_key].append((org_key, node_title))
    return node_to_orgs


def read_publisher_stats(path: Path) -> Dict[str, Dict[str, float]]:
    # TSV with headers; treat quotes as literal
    data: Dict[str, Dict[str, float]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in r:
            key = (row.get("publishingorgkey") or row.get("publishingOrgKey") or "").strip()
            if not key:
                continue
            rec: Dict[str, float] = {}
            for col in NUM_COLS:
                val = row.get(col) or row.get(col.lower()) or row.get(col.upper())
                try:
                    rec[col] = float(val)
                except Exception:
                    rec[col] = 0.0
            data[key] = rec
    return data


def write_node_aggregates(node_to_orgs: Dict[str, List[Tuple[str, str]]], pub_stats: Dict[str, Dict[str, float]], nodes_json_path: Path, out_csv: Path) -> None:
    # Load node titles from nodes.json for consistent naming
    import json
    nodes = json.loads(nodes_json_path.read_text(encoding="utf-8")) if nodes_json_path.exists() else []
    node_title_by_key = {str(n.get("nodeKey")): n.get("nodeTitle") for n in nodes}

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        headers = [
            "nodeKey",
            "nodeTitle",
            "total_records",
            "records_with_recordedbyid",
            "pct_with_recordedbyid",
            "records_with_valid_recordedbyid",
            "pct_valid_recordedbyid",
            "records_with_invalid_recordedbyid",
            "pct_invalid_recordedbyid",
            "records_with_orcid",
            "pct_with_orcid",
            "records_with_google_scholar",
            "pct_with_google_scholar",
            "records_with_researcherid",
            "pct_with_researcherid",
            "records_with_wikidata",
            "pct_with_wikidata",
            "records_with_linkedin",
            "pct_with_linkedin",
            "orgCount",
        ]
        w.writerow(headers)

        for node_key, orgs in node_to_orgs.items():
            sums = {c: 0.0 for c in NUM_COLS}
            org_count = 0
            for org_key, _node_title in orgs:
                stats = pub_stats.get(org_key)
                if not stats:
                    continue
                org_count += 1
                for c in NUM_COLS:
                    sums[c] += float(stats.get(c, 0.0))

            total = sums["total_records"] or 0.0
            def pct(num):
                return (100.0 * num / total) if total > 0 else 0.0

            row = [
                node_key,
                node_title_by_key.get(node_key) or (orgs[0][1] if orgs else node_key),
                int(sums["total_records"]),
                int(sums["records_with_recordedbyid"]),
                pct(sums["records_with_recordedbyid"]),
                int(sums["records_with_valid_recordedbyid"]),
                pct(sums["records_with_valid_recordedbyid"]),
                int(sums["records_with_invalid_recordedbyid"]),
                pct(sums["records_with_invalid_recordedbyid"]),
                int(sums["records_with_orcid"]),
                pct(sums["records_with_orcid"]),
                int(sums["records_with_google_scholar"]),
                pct(sums["records_with_google_scholar"]),
                int(sums["records_with_researcherid"]),
                pct(sums["records_with_researcherid"]),
                int(sums["records_with_wikidata"]),
                pct(sums["records_with_wikidata"]),
                int(sums["records_with_linkedin"]),
                pct(sums["records_with_linkedin"]),
                org_count,
            ]
            w.writerow(row)


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aggregate publisher stats by GBIF Node")
    p.add_argument("--node-org-map", dest="node_org_map", type=Path, default=Path("out-nodes/node-org-map.csv"), help="Path to node-org mapping CSV")
    p.add_argument("--publisher-stats-tsv", dest="publisher_stats_tsv", type=Path, default=Path("out-recordedby_publisher/0052593-251009101135966.csv"), help="Publisher TSV stats file")
    p.add_argument("--nodes-json", dest="nodes_json", type=Path, default=Path("out-nodes/nodes.json"), help="Nodes JSON with organizations")
    p.add_argument("--out-csv", dest="out_csv", type=Path, default=Path("out-by-node/recordedby_by_node.csv"), help="Output CSV path")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    node_to_orgs = read_node_org_map(args.node_org_map)
    pub_stats = read_publisher_stats(args.publisher_stats_tsv)
    write_node_aggregates(node_to_orgs, pub_stats, args.nodes_json, args.out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


