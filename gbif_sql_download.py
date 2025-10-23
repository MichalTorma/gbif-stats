#!/usr/bin/env python3
import argparse
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional, Tuple

try:
    import requests
    from requests.auth import HTTPBasicAuth
except Exception as exc:  # pragma: no cover
    print("Missing dependency: requests. Please run 'pip install -r requirements.txt'", file=sys.stderr)
    raise


GBIF_API_BASE = "https://api.gbif.org/v1"


def read_sql_file(sql_path: Path, strip_comments: bool) -> str:
    sql_text = sql_path.read_text(encoding="utf-8")
    if strip_comments:
        # Remove lines beginning with SQL comment marker "--"
        filtered_lines = []
        for line in sql_text.splitlines():
            if line.lstrip().startswith("--"):
                continue
            filtered_lines.append(line)
        sql_text = "\n".join(filtered_lines)
    return sql_text


def build_request_body(sql_text: str, send_notification: bool, notification_email: Optional[str], download_format: str) -> dict:
    body = {
        "sendNotification": bool(send_notification),
        "format": download_format,
        "sql": sql_text,
    }
    if send_notification and notification_email:
        body["notificationAddresses"] = [notification_email]
    return body


def validate_sql(body: dict, timeout_s: int) -> Tuple[bool, Optional[str]]:
    url = f"{GBIF_API_BASE}/occurrence/download/request/validate"
    try:
        resp = requests.post(url, json=body, headers={"Content-Type": "application/json"}, timeout=timeout_s)
    except Exception as exc:  # pragma: no cover
        return False, f"Validation request failed: {exc}"

    # Treat any 2xx as a successful validation (GBIF may return 200/201/etc.)
    if 200 <= resp.status_code < 300:
        return True, None
    # GBIF returns an error message in JSON or text when invalid
    try:
        return False, resp.json().get("message") or resp.text
    except Exception:
        return False, resp.text


def submit_download(body: dict, username: str, password: str, timeout_s: int) -> str:
    url = f"{GBIF_API_BASE}/occurrence/download/request"
    resp = requests.post(
        url,
        json=body,
        headers={"Content-Type": "application/json"},
        auth=HTTPBasicAuth(username, password),
        timeout=timeout_s,
    )
    if resp.status_code not in (201, 202):
        raise RuntimeError(f"Request failed ({resp.status_code}): {resp.text}")
    # API returns the download key as plain text body
    key = resp.text.strip().strip('"')
    if not key:
        raise RuntimeError("Empty download key returned from GBIF API")
    return key


def poll_until_done(key: str, poll_interval_s: int, max_wait_s: int) -> dict:
    url = f"{GBIF_API_BASE}/occurrence/download/{key}"
    start_time = time.time()
    last_status = None
    while True:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Polling failed ({resp.status_code}): {resp.text}")
        info = resp.json()
        status = (info.get("status") or "").upper()
        if status != last_status:
            print(f"Status: {status}")
            last_status = status
        if status in ("SUCCEEDED", "CANCELLED", "KILLED", "FAILED"):
            return info
        if time.time() - start_time > max_wait_s:
            raise TimeoutError(f"Timed out after {max_wait_s}s waiting for download {key}")
        time.sleep(poll_interval_s)


def compute_zip_url(key: str) -> str:
    # As per docs, the file can be downloaded from this URL
    return f"{GBIF_API_BASE}/occurrence/download/request/{key}.zip"


def download_zip(key: str, destination: Path, timeout_s: int) -> Path:
    url = compute_zip_url(key)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout_s) as r:
        r.raise_for_status()
        with open(destination, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return destination


def extract_zip(zip_path: Path, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Submit a GBIF SQL download request from a .sql file, optionally validate, poll, download, and extract the result."
    )
    parser.add_argument("sql_file", type=Path, help="Path to the .sql file containing a single SELECT query against the occurrence table")
    parser.add_argument("--username", "-u", help="GBIF.org username. Can also be set via GBIF_USERNAME env var")
    parser.add_argument("--password", "-p", help="GBIF.org password. Can also be set via GBIF_PASSWORD env var")

    parser.add_argument("--send-notification", action="store_true", help="Request GBIF to send an email notification when ready")
    parser.add_argument("--email", help="Notification email address (used only if --send-notification is set)")

    parser.add_argument("--format", default="SQL_TSV_ZIP", help="Download format. Default: SQL_TSV_ZIP")
    parser.add_argument("--strip-comments", action="store_true", help="Strip '--' SQL comment lines before submission")

    parser.add_argument("--validate-only", action="store_true", help="Validate the SQL only and exit")
    parser.add_argument("--poll", action="store_true", help="Poll the request until it completes")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between poll checks. Default: 30")
    parser.add_argument("--max-wait", type=int, default=3600, help="Max seconds to wait while polling. Default: 3600")

    parser.add_argument("--download", action="store_true", help="Download the resulting ZIP when ready")
    parser.add_argument("--output", type=Path, default=Path("gbif_sql_download.zip"), help="Output ZIP path. Default: gbif_sql_download.zip")
    parser.add_argument("--extract", type=Path, help="If set, extract the ZIP into this directory after download")

    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout (seconds) for API requests. Default: 60")

    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)

    if not args.sql_file.exists():
        print(f"SQL file not found: {args.sql_file}", file=sys.stderr)
        return 2

    sql_text = read_sql_file(args.sql_file, strip_comments=args.strip_comments)
    body = build_request_body(sql_text, args.send_notification, args.email, args.format)

    # Validate first unless user chooses to skip
    print("Validating SQL...")
    is_valid, error_message = validate_sql(body, timeout_s=args.timeout)
    if not is_valid:
        print("Validation failed:")
        print(error_message or "Unknown error")
        return 1
    print("Validation OK")

    if args.validate_only:
        return 0

    username = args.username or os.environ.get("GBIF_USERNAME")
    password = args.password or os.environ.get("GBIF_PASSWORD")
    if not username or not password:
        print("Missing credentials. Provide --username/--password or set GBIF_USERNAME/GBIF_PASSWORD.", file=sys.stderr)
        return 2

    print("Submitting download request...")
    key = submit_download(body, username=username, password=password, timeout_s=args.timeout)
    print(f"Download key: {key}")

    if not args.poll and not args.download and not args.extract:
        print("Hint: use --poll to wait for completion, and --download to fetch the ZIP.")
        return 0

    info = poll_until_done(key, poll_interval_s=args.poll_interval, max_wait_s=args.max_wait)
    status = (info.get("status") or "").upper()
    if status != "SUCCEEDED":
        print(f"Download did not succeed. Final status: {status}")
        return 3

    if args.download or args.extract:
        print("Downloading ZIP...")
        zip_path = download_zip(key, destination=args.output, timeout_s=max(args.timeout, 120))
        print(f"Saved: {zip_path}")
        if args.extract:
            print(f"Extracting into: {args.extract}")
            extract_zip(zip_path, args.extract)
            print("Extraction complete")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


