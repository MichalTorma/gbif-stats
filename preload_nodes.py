#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests


GBIF_API_BASE = "https://api.gbif.org/v1"


def request_with_retry(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 20, retries: int = 4, backoff: float = 0.8) -> requests.Response:
    attempt = 0
    while True:
        try:
            resp = requests.get(url, headers=headers or {}, timeout=timeout)
            return resp
        except requests.RequestException:
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(backoff * (2 ** (attempt - 1)))


def fetch_json(url: str, etag_cache: Dict[str, str], timeout: int = 20) -> Any:
    headers: Dict[str, str] = {}
    if url in etag_cache and etag_cache[url]:
        headers["If-None-Match"] = etag_cache[url]

    resp = request_with_retry(url, headers=headers, timeout=timeout)
    if resp.status_code == 304:
        # Not modified; caller should use prior cached body (handled by caller)
        return None
    resp.raise_for_status()
    etag = resp.headers.get("ETag")
    if etag:
        etag_cache[url] = etag
    return resp.json()


def load_cache(cache_file: Path) -> Dict[str, Any]:
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return {"etag": {}, "bodies": {}}
    return {"etag": {}, "bodies": {}}


def save_cache(cache_file: Path, cache: Dict[str, Any]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def get_active_nodes(base: str, cache: Dict[str, Any], timeout: int) -> List[Dict[str, Any]]:
    url = f"{base}/node?limit=1000&status=ACTIVE"
    data = fetch_json(url, cache.setdefault("etag", {}), timeout=timeout)
    if data is None:
        body = cache.get("bodies", {}).get(url)
        if body is None:
            raise RuntimeError("ETag indicated not modified, but cache body missing for nodes list")
        data = body
    # Registry lists often return objects with 'results'; sometimes APIs return arrays. Handle both
    if isinstance(data, dict) and "results" in data:
        results = data.get("results") or []
    elif isinstance(data, list):
        results = data
    else:
        results = []
    cache.setdefault("bodies", {})[url] = data
    return results


def get_node_orgs(base: str, node_key: str, cache: Dict[str, Any], timeout: int) -> List[Dict[str, Any]]:
    # Handle pagination defensively
    all_orgs: List[Dict[str, Any]] = []
    offset = 0
    limit = 1000
    while True:
        url = f"{base}/node/{node_key}/organization?limit={limit}&offset={offset}"
        data = fetch_json(url, cache.setdefault("etag", {}), timeout=timeout)
        if data is None:
            body = cache.get("bodies", {}).get(url)
            if body is None:
                raise RuntimeError(f"ETag not modified but cache missing for {url}")
            data = body
        # Results may be dict with results or array
        if isinstance(data, dict) and "results" in data:
            results = data.get("results") or []
            end_of_records = bool(data.get("endOfRecords", False))
        elif isinstance(data, list):
            results = data
            end_of_records = len(results) < limit
        else:
            results = []
            end_of_records = True
        cache.setdefault("bodies", {})[url] = data

        all_orgs.extend(results)
        if end_of_records or len(results) == 0:
            break
        offset += limit
    return all_orgs


def write_outputs(nodes: List[Dict[str, Any]], node_orgs: Dict[str, List[Dict[str, Any]]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes_json = []
    for n in nodes:
        key = str(n.get("key"))
        title = n.get("title") or n.get("name") or key
        orgs = node_orgs.get(key, [])
        nodes_json.append({
            "nodeKey": key,
            "nodeTitle": title,
            "organizations": [
                {"key": str(o.get("key")), "title": o.get("title") or o.get("name") or str(o.get("key"))}
                for o in orgs
            ],
        })

    (out_dir / "nodes.json").write_text(json.dumps(nodes_json, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV map
    import csv
    with (out_dir / "node-org-map.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nodeKey", "nodeTitle", "publishingOrgKey", "publisherName"])
        for n in nodes_json:
            for o in n["organizations"]:
                w.writerow([n["nodeKey"], n["nodeTitle"], o["key"], o["title"]])


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Preload GBIF active nodes and endorsed organizations")
    p.add_argument("--base-url", default=GBIF_API_BASE)
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("--cache-file", type=Path, default=Path("out-nodes/.registry_cache.json"))
    p.add_argument("--out-dir", type=Path, default=Path("out-nodes"))
    p.add_argument("--no-cache", action="store_true", help="Ignore ETag cache and fetch fresh")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cache = {"etag": {}, "bodies": {}}
    if not args.no_cache:
        cache = load_cache(args.cache_file)

    try:
        nodes = get_active_nodes(args.base_url, cache, timeout=args.timeout)
        node_orgs: Dict[str, List[Dict[str, Any]]] = {}
        for n in nodes:
            key = str(n.get("key"))
            orgs = get_node_orgs(args.base_url, key, cache, timeout=args.timeout)
            node_orgs[key] = orgs
        write_outputs(nodes, node_orgs, args.out_dir)
    finally:
        save_cache(args.cache_file, cache)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


