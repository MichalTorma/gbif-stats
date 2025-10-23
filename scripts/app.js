/* globals Papa, Chart */

// Copied from web/app.js with paths adjusted for root-based hosting
(function () {
  const PATHS = {
    // relative to repo root
    publisher: "out-recordedby_publisher/0052593-251009101135966.csv",
    hosting: "out-recordedby_hostingorg/0051475-251009101135966-enriched.csv",
  };

  const STATE = {
    activeTab: "publisher",
    data: { publisher: [], hosting: [] },
    filtered: [],
    selection: null,
    chart: null,
  };

  const els = {
    tabPublisher: document.getElementById("tab-publisher"),
    tabHosting: document.getElementById("tab-hosting"),
    search: document.getElementById("search-input"),
    sort: document.getElementById("sort-select"),
    list: document.getElementById("entity-list"),
    canvas: document.getElementById("pie-canvas"),
    meta: document.getElementById("detail-meta"),
  };

  function parseNumber(value) {
    if (value === null || value === undefined) return 0;
    const v = String(value).replace(/,/g, "").trim();
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  }

  function normalizeRowPublisher(row) {
    return {
      key: row.publishingorgkey || row["publishingorgkey"],
      name: row.publishername || row["publishername"],
      url: row.publisherurl || row["publisherurl"],
      total_records: parseNumber(row.total_records || row["total_records"]),
      records_with_recordedbyid: parseNumber(row.records_with_recordedbyid || row["records_with_recordedbyid"]),
      pct_with_recordedbyid: parseNumber(row.pct_with_recordedbyid || row["pct_with_recordedbyid"]),
      records_with_valid_recordedbyid: parseNumber(row.records_with_valid_recordedbyid || row["records_with_valid_recordedbyid"]),
      pct_valid_recordedbyid: parseNumber(row.pct_valid_recordedbyid || row["pct_valid_recordedbyid"]),
      records_with_invalid_recordedbyid: parseNumber(row.records_with_invalid_recordedbyid || row["records_with_invalid_recordedbyid"]),
      pct_invalid_recordedbyid: parseNumber(row.pct_invalid_recordedbyid || row["pct_invalid_recordedbyid"]),
      records_with_orcid: parseNumber(row.records_with_orcid || row["records_with_orcid"]),
      pct_with_orcid: parseNumber(row.pct_with_orcid || row["pct_with_orcid"]),
      records_with_google_scholar: parseNumber(row.records_with_google_scholar || row["records_with_google_scholar"]),
      pct_with_google_scholar: parseNumber(row.pct_with_google_scholar || row["pct_with_google_scholar"]),
      records_with_researcherid: parseNumber(row.records_with_researcherid || row["records_with_researcherid"]),
      pct_with_researcherid: parseNumber(row.pct_with_researcherid || row["pct_with_researcherid"]),
      records_with_wikidata: parseNumber(row.records_with_wikidata || row["records_with_wikidata"]),
      pct_with_wikidata: parseNumber(row.pct_with_wikidata || row["pct_with_wikidata"]),
      records_with_linkedin: parseNumber(row.records_with_linkedin || row["records_with_linkedin"]),
      pct_with_linkedin: parseNumber(row.pct_with_linkedin || row["pct_with_linkedin"]),
    };
  }

  function normalizeRowHosting(row) {
    return {
      key: row.hostingorganizationkey || row["hostingorganizationkey"],
      name: row.publisherName || row["publisherName"] || row.publishername || row["publishername"] || row.hostingorganizationkey,
      url: row.publisherUrl || row["publisherUrl"] || (row.hostingorganizationkey ? `https://www.gbif.org/publisher/${row.hostingorganizationkey}` : ""),
      total_records: parseNumber(row.total_records || row["total_records"]),
      records_with_recordedbyid: parseNumber(row.records_with_recordedbyid || row["records_with_recordedbyid"]),
      pct_with_recordedbyid: parseNumber(row.pct_with_recordedbyid || row["pct_with_recordedbyid"]),
      records_with_valid_recordedbyid: parseNumber(row.records_with_valid_recordedbyid || row["records_with_valid_recordedbyid"]),
      pct_valid_recordedbyid: parseNumber(row.pct_valid_recordedbyid || row["pct_valid_recordedbyid"]),
      records_with_invalid_recordedbyid: parseNumber(row.records_with_invalid_recordedbyid || row["records_with_invalid_recordedbyid"]),
      pct_invalid_recordedbyid: parseNumber(row.pct_invalid_recordedbyid || row["pct_invalid_recordedbyid"]),
      records_with_orcid: parseNumber(row.records_with_orcid || row["records_with_orcid"]),
      pct_with_orcid: parseNumber(row.pct_with_orcid || row["pct_with_orcid"]),
      records_with_google_scholar: parseNumber(row.records_with_google_scholar || row["records_with_google_scholar"]),
      pct_with_google_scholar: parseNumber(row.pct_with_google_scholar || row["pct_with_google_scholar"]),
      records_with_researcherid: parseNumber(row.records_with_researcherid || row["records_with_researcherid"]),
      pct_with_researcherid: parseNumber(row.pct_with_researcherid || row["pct_with_researcherid"]),
      records_with_wikidata: parseNumber(row.records_with_wikidata || row["records_with_wikidata"]),
      pct_with_wikidata: parseNumber(row.pct_with_wikidata || row["pct_with_wikidata"]),
      records_with_linkedin: parseNumber(row.records_with_linkedin || row["records_with_linkedin"]),
      pct_with_linkedin: parseNumber(row.pct_with_linkedin || row["pct_with_linkedin"]),
    };
  }

  function toDisplayRows(kind) {
    const src = STATE.data[kind] || [];
    const rows = src.map(r => ({ ...r }));
    return rows;
  }

  function sortRows(rows, sortKey, dir) {
    const mul = dir === "asc" ? 1 : -1;
    rows.sort((a, b) => {
      const av = parseNumber(a[sortKey]);
      const bv = parseNumber(b[sortKey]);
      if (av === bv) {
        const a2 = parseNumber(a.records_with_valid_recordedbyid);
        const b2 = parseNumber(b.records_with_valid_recordedbyid);
        if (a2 === b2) {
          const a3 = parseNumber(a.total_records);
          const b3 = parseNumber(b.total_records);
          return b3 - a3;
        }
        return b2 - a2;
      }
      return (av - bv) * mul;
    });
  }

  function renderList() {
    const query = (els.search.value || "").toLowerCase();
    const [sortKey, sortDir] = (els.sort.value || "pct_valid_recordedbyid-desc").split("-");
    const rows = toDisplayRows(STATE.activeTab).filter(r => !query || (r.name || "").toLowerCase().includes(query));
    sortRows(rows, sortKey, sortDir);
    STATE.filtered = rows;

    els.list.innerHTML = "";
    rows.forEach((r, idx) => {
      const item = document.createElement("div");
      item.className = "list-item" + (STATE.selection && STATE.selection.key === r.key ? " active" : "");
      item.setAttribute("role", "button");
      item.setAttribute("tabindex", "0");
      item.addEventListener("click", () => selectRow(r));
      item.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); selectRow(r); } });

      const title = document.createElement("div");
      title.className = "item-title";
      title.textContent = r.name || r.key || `Item ${idx+1}`;

      const pct = document.createElement("div");
      pct.className = "pill accent";
      pct.textContent = `${(parseNumber(r.pct_valid_recordedbyid)).toFixed(2)}% valid`;

      const counts = document.createElement("div");
      counts.className = "pill";
      counts.textContent = `${r.records_with_valid_recordedbyid} / ${r.total_records}`;

      item.appendChild(title);
      item.appendChild(pct);
      item.appendChild(counts);
      els.list.appendChild(item);
    });

    if (!STATE.selection && rows.length) {
      selectRow(rows[0]);
    }
  }

  function selectRow(row) {
    STATE.selection = row;
    Array.from(els.list.children).forEach((el) => el.classList.remove("active"));
    const match = Array.from(els.list.children).find(el => (el.querySelector(".item-title")?.textContent || "") === (row.name || row.key));
    if (match) match.classList.add("active");

    renderChart(row);
    renderMeta(row);
  }

  function renderMeta(row) {
    const parts = [];
    if (row.name) parts.push(`<strong>${escapeHtml(row.name)}</strong>`);
    if (row.url) parts.push(`<a href="${encodeURI(row.url)}" target="_blank" rel="noreferrer noopener">GBIF page</a>`);
    parts.push(`<span>Total: ${row.total_records.toLocaleString()}</span>`);
    parts.push(`<span>With recordedById: ${row.records_with_recordedbyid.toLocaleString()} (${row.pct_with_recordedbyid.toFixed(2)}%)</span>`);
    els.meta.innerHTML = parts.join(" • ");
  }

  function renderChart(row) {
    const valid = parseNumber(row.records_with_valid_recordedbyid);
    const invalid = parseNumber(row.records_with_invalid_recordedbyid);
    const withId = parseNumber(row.records_with_recordedbyid);
    const none = Math.max(0, parseNumber(row.total_records) - withId);

    const orcid = parseNumber(row.records_with_orcid);
    const gscholar = parseNumber(row.records_with_google_scholar);
    const researcherid = parseNumber(row.records_with_researcherid);
    const wikidata = parseNumber(row.records_with_wikidata);
    const linkedin = parseNumber(row.records_with_linkedin);

    const knownSum = orcid + gscholar + researcherid + wikidata + linkedin;
    const otherValid = Math.max(0, valid - knownSum);

    const labels = [
      "ORCID",
      "Google Scholar",
      "ResearcherID",
      "Wikidata",
      "LinkedIn",
      "Other valid",
      "Invalid",
      "None",
    ];
    const values = [
      orcid,
      gscholar,
      researcherid,
      wikidata,
      linkedin,
      otherValid,
      invalid,
      none,
    ];
    const colors = [
      "#7ed3b2",
      "#5b8cff",
      "#8e87ff",
      "#f2a97f",
      "#e67dd5",
      "#4fd1c5",
      "#ff6b6b",
      "#a8b3cf",
    ];

    const total = values.reduce((a, b) => a + b, 0);
    const data = { labels, datasets: [{ data: values, backgroundColor: colors }] };
    const cfg = {
      type: "pie",
      data,
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { color: "#e2e8f0" } },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const val = ctx.parsed;
                const pct = total > 0 ? (val / total) * 100 : 0;
                return `${ctx.label}: ${val.toLocaleString()} (${pct.toFixed(2)}%)`;
              },
            },
          },
        },
      },
    };

    if (STATE.chart) {
      STATE.chart.data = data;
      STATE.chart.update();
    } else {
      STATE.chart = new Chart(els.canvas, cfg);
    }
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]+/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
  }

  function setActiveTab(tab) {
    if (STATE.activeTab === tab) return;
    STATE.activeTab = tab;
    els.tabPublisher.classList.toggle("active", tab === "publisher");
    els.tabHosting.classList.toggle("active", tab === "hosting");
    renderList();
  }

  function wireEvents() {
    els.tabPublisher.addEventListener("click", () => setActiveTab("publisher"));
    els.tabHosting.addEventListener("click", () => setActiveTab("hosting"));
    els.search.addEventListener("input", () => renderList());
    els.sort.addEventListener("change", () => renderList());
  }

  function loadCsv(path, normalizeFn, configOverrides = {}) {
    return new Promise((resolve, reject) => {
      Papa.parse(path, {
        header: true,
        dynamicTyping: false,
        skipEmptyLines: true,
        download: true,
        ...configOverrides,
        complete: (res) => {
          const rows = (res.data || []).map(normalizeFn).filter(r => r && r.key);
          resolve(rows);
        },
        error: (err) => reject(err),
      });
    });
  }

  async function init() {
    wireEvents();

    try {
      const [pubRows, hostRows] = await Promise.all([
        loadCsv(PATHS.publisher, normalizeRowPublisher, { delimiter: "\t", quoteChar: '', escapeChar: '' }),
        loadCsv(PATHS.hosting, normalizeRowHosting),
      ]);
      STATE.data.publisher = pubRows;
      STATE.data.hosting = hostRows;
      renderList();
    } catch (e) {
      console.error("Failed to load CSVs", e);
      els.list.innerHTML = `<div style="padding:12px;color:#f88">Failed to load CSVs. Check paths in scripts/app.js.</div>`;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();


