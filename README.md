## GBIF SQL Download CLI

Simple CLI to submit GBIF SQL downloads from a .sql file, poll until completion, and download/extract the result.

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage

Prepare a file like `query.sql` containing a single SELECT against the `occurrence` table. See the GBIF docs for supported SQL and columns: [API SQL Downloads](https://techdocs.gbif.org/en/data-use/api-sql-downloads#sql).

Set credentials (username, not email) via flags or env vars:

```bash
export GBIF_USERNAME=your_username
export GBIF_PASSWORD=your_password
```

Validate only:

```bash
python gbif_sql_download.py query.sql --strip-comments --validate-only
```

Submit, poll, and download ZIP (and extract to a folder):

```bash
python gbif_sql_download.py query.sql \
  --strip-comments \
  --poll --download --extract out_dir \
  --output result.zip
```

Options:

```bash
python gbif_sql_download.py --help
```

Notes:
- Format defaults to `SQL_TSV_ZIP` as per GBIF docs.
- You may request email notifications using `--send-notification --email you@example.org`.
- The tool removes `--` comment lines with `--strip-comments` to satisfy GBIF validator constraints.

Documentation reference: [GBIF API SQL Downloads](https://techdocs.gbif.org/en/data-use/api-sql-downloads#sql).



## Web visualization

Static viewer is at repo root (`index.html`) and loads the CSVs directly from `out-recordedby_publisher/` and `out-recordedby_hostingorg/`. Assets are in `scripts/`.

Serve locally (from repo root):

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

Deploy on GitHub Pages:
- Push to a branch and enable Pages for the repository (Deploy from Branch) targeting the root.
- The page will be served from `/index.html` and fetch the CSVs at `out-recordedby_*` paths.

Features:
- Toggle tabs: by publisher or by hosting org
- Search filter and sort (default: pct valid desc, then valid count desc)
- Click an item to see a pie chart showing: ORCID, Google Scholar, ResearcherID, Wikidata, LinkedIn, Other valid, Invalid, None
- Actions panel: open GBIF SQL with pre-filled queries for Valid / Invalid / Missing

### By GBIF Node (preload)

1) Preload nodes and endorsed organizations:

```bash
python preload_nodes.py --timeout 30
```

Outputs:
- `out-nodes/nodes.json`
- `out-nodes/node-org-map.csv`

2) Aggregate existing publisher stats to Node-level:

```bash
python aggregate_by_node.py \
  out-nodes/node-org-map.csv \
  out-recordedby_publisher/0052593-251009101135966.csv \
  out-nodes/nodes.json \
  out-by-node/recordedby_by_node.csv
```

3) Open the site; select the "By node" tab.

Notes:
- SQL links for nodes use `publishingOrgKey IN (...)` with all endorsed organizations. Very large lists may exceed URL length limits in browsers.

