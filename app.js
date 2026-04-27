// ══════════════════════════════════════════════════════
// STATE
// ══════════════════════════════════════════════════════

let state = {
  seriesIndex: null,
  view: "grid",
  keyOnly: false,
  variantOnly: false,
  sort: "default",
  issueSearch: "",
};

// ══════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  // Drop zone events
  const dropZone = document.getElementById("dropZone");

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone.addEventListener("dragleave", () =>
    dropZone.classList.remove("drag-over"),
  );
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  document.getElementById("fileInputDrop").addEventListener("change", (e) => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
  });

  document.getElementById("fileInputHeader").addEventListener("change", (e) => {
    if (e.target.files[0]) handleFile(e.target.files[0], true);
    e.target.value = "";
  });

  // Search & sort (wired once; app div is hidden until data loaded)
  document.getElementById("issueSearch").addEventListener("input", (e) => {
    state.issueSearch = e.target.value.toLowerCase();
    renderIssues();
  });

  document.getElementById("sortSelect").addEventListener("change", (e) => {
    state.sort = e.target.value;
    renderIssues();
  });
});

// ══════════════════════════════════════════════════════
// FILE / UPLOAD HANDLING
// ══════════════════════════════════════════════════════

function handleFile(file, isReplace = false) {
  const errEl = document.getElementById("uploadError");
  if (errEl) errEl.textContent = "";

  if (!file.name.endsWith(".json") && file.type !== "application/json") {
    showUploadError("Please select a .json file.");
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result);
      if (!Array.isArray(data)) throw new Error("Expected a JSON array");
      if (data.length === 0)
        throw new Error("The file contains no series data");
      window.COMICS_DATA = data;
      launchApp(isReplace);
    } catch (err) {
      showUploadError("Invalid JSON: " + err.message);
    }
  };
  reader.onerror = () => showUploadError("Could not read the file.");
  reader.readAsText(file);
}

function showUploadError(msg) {
  const el = document.getElementById("uploadError");
  if (el) el.textContent = msg;
}

function loadDemo() {
  // COMICS_DATA is already defined in data.js as sample data
  launchApp(false);
}

function launchApp(isReplace) {
  document.getElementById("uploadScreen").classList.remove("visible");
  document.getElementById("app").style.display = "block";

  // Reset state on fresh load
  state.seriesIndex = null;
  state.keyOnly = false;
  state.variantOnly = false;
  state.sort = "default";
  state.issueSearch = "";
  state.view = "grid";
  document.getElementById("issueSearch").value = "";
  document.getElementById("sortSelect").value = "default";
  document.getElementById("keyToggle").classList.remove("on");
  document.getElementById("variantToggle").classList.remove("on");

  renderSeriesList();
  if (window.COMICS_DATA.length > 0) selectSeries(0);
}

// ══════════════════════════════════════════════════════
// SERIES LIST
// ══════════════════════════════════════════════════════

function renderSeriesList() {
  const data = window.COMICS_DATA;
  const container = document.getElementById("seriesList");
  const totalSeries = data.length;
  const totalKeys = data.reduce((s, d) => s + (d.key_issues || 0), 0);

  document.getElementById("headerStats").innerHTML =
    `<strong>${totalSeries}</strong> series &nbsp;·&nbsp; <strong>${totalKeys}</strong> key issues`;

  container.innerHTML = data
    .map(
      (s, i) => `
        <div class="series-item ${state.seriesIndex === i ? "active" : ""}" onclick="selectSeries(${i})">
          <div class="series-name">${esc(s.title)}</div>
          <div class="series-meta">
            <span class="series-pub">${esc(s.publisher)}</span>
            ${s.dates ? `<span class="series-dates">${esc(s.dates)}</span>` : ""}
            ${s.key_issues ? `<span class="badge badge-key">★ ${s.key_issues}</span>` : ""}
            ${s.total_issues ? `<span class="badge badge-total">${s.total_issues} iss</span>` : ""}
          </div>
        </div>
      `,
    )
    .join("");
}

// ══════════════════════════════════════════════════════
// SELECT SERIES
// ══════════════════════════════════════════════════════

function selectSeries(index) {
  state.seriesIndex = index;
  state.issueSearch = "";
  document.getElementById("issueSearch").value = "";
  renderSeriesList();
  renderIssues();
}

// ══════════════════════════════════════════════════════
// RENDER ISSUES
// ══════════════════════════════════════════════════════

function renderIssues() {
  const content = document.getElementById("mainContent");
  if (state.seriesIndex === null) return;

  const series = window.COMICS_DATA[state.seriesIndex];
  let issues = [...(series.issues || [])];

  // Filter
  if (state.keyOnly) issues = issues.filter((i) => i.is_key);
  if (state.variantOnly) issues = issues.filter((i) => i.has_variants);
  if (state.issueSearch) {
    issues = issues.filter(
      (i) =>
        i.title.toLowerCase().includes(state.issueSearch) ||
        (i.key_notes || []).some((n) =>
          n.toLowerCase().includes(state.issueSearch),
        ) ||
        (i.tags || []).some((t) => t.toLowerCase().includes(state.issueSearch)),
    );
  }

  // Sort
  if (state.sort === "price-high") {
    issues.sort((a, b) => parseMoney(b.price_mid) - parseMoney(a.price_mid));
  } else if (state.sort === "price-low") {
    issues.sort((a, b) => parseMoney(a.price_mid) - parseMoney(b.price_mid));
  } else if (state.sort === "title") {
    issues.sort((a, b) => a.title.localeCompare(b.title));
  }

  const keyCount = issues.filter((i) => i.is_key).length;

  content.innerHTML = `
    <div class="series-header">
      <div class="series-title">${esc(series.title)}</div>
      <div class="series-subtitle">
        <strong>${esc(series.publisher)}</strong>
        ${series.dates ? `<span>${esc(series.dates)}</span>` : ""}
        ${series.key_issues ? `<span class="badge badge-key">★ ${series.key_issues} keys</span>` : ""}
        ${series.total_issues ? `<span class="badge badge-total">${series.total_issues} total issues</span>` : ""}
      </div>
    </div>
    <hr class="divider">
    <div class="view-controls">
      <button class="view-btn ${state.view === "grid" ? "active" : ""}" onclick="setView('grid')">
        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
        Grid
      </button>
      <button class="view-btn ${state.view === "list" ? "active" : ""}" onclick="setView('list')">
        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
        List
      </button>
      <span class="issue-count-label">${issues.length} issue${issues.length !== 1 ? "s" : ""} · ${keyCount} key${keyCount !== 1 ? "s" : ""}</span>
    </div>
    ${
      issues.length === 0
        ? `<div class="no-issues">No issues match the current filters.</div>`
        : state.view === "grid"
          ? `<div class="issues-grid">${issues.map(renderCardHtml).join("")}</div>`
          : `<div class="issues-list">${issues.map(renderRowHtml).join("")}</div>`
    }
  `;
}

function renderCardHtml(issue) {
  return `
    <div class="issue-card ${issue.is_key ? "key-issue" : ""}" onclick='openModal(${JSON.stringify(issue)})'>
      ${
        issue.cover_image
          ? `<img class="issue-cover" src="${esc(issue.cover_image)}" alt="${esc(issue.title)}" loading="lazy">`
          : `<div class="cover-placeholder">
               <span class="issue-num">#</span>
               <span style="font-size:11px;color:var(--muted);font-family:var(--font-cond);">${esc(issue.title.replace(/.*#/, "#"))}</span>
             </div>`
      }
      ${issue.is_key ? `<div class="key-ribbon">KEY</div>` : ""}
      <div class="issue-info">
        <div class="issue-title-text">${esc(issue.title)}</div>
        ${
          issue.price_low || issue.price_mid || issue.price_high
            ? `<div class="price-row">
                 ${issue.price_low ? `<span class="price price-low">${esc(issue.price_low)}</span><span class="price-sep">·</span>` : ""}
                 ${issue.price_mid ? `<span class="price price-mid">${esc(issue.price_mid)}</span>` : ""}
                 ${issue.price_high ? `<span class="price-sep">·</span><span class="price price-high">${esc(issue.price_high)}</span>` : ""}
               </div>`
            : ""
        }
        <div class="tag-row">
          ${(issue.tags || [])
            .slice(0, 3)
            .map((t) => `<span class="tag">${esc(t)}</span>`)
            .join("")}
          ${issue.has_variants ? `<span class="variant-badge">${issue.variant_count} variants</span>` : ""}
        </div>
      </div>
    </div>
  `;
}

function renderRowHtml(issue) {
  return `
    <div class="issue-row ${issue.is_key ? "key-issue" : ""}" onclick='openModal(${JSON.stringify(issue)})'>
      ${
        issue.cover_image
          ? `<img class="row-cover" src="${esc(issue.cover_image)}" alt="" loading="lazy">`
          : `<div class="row-cover-placeholder">#</div>`
      }
      <div class="row-info">
        <div class="row-title">
          ${esc(issue.title)}
          ${issue.is_key ? `<span class="badge badge-key" style="vertical-align:middle;">★ KEY</span>` : ""}
        </div>
        ${issue.key_notes && issue.key_notes[0] ? `<div class="row-notes">${esc(issue.key_notes[0])}</div>` : ""}
        <div class="tag-row">
          ${(issue.tags || [])
            .slice(0, 4)
            .map((t) => `<span class="tag">${esc(t)}</span>`)
            .join("")}
          ${issue.has_variants ? `<span class="variant-badge">${issue.variant_count} variants</span>` : ""}
        </div>
      </div>
      <div class="row-prices">
        ${issue.price_mid ? `<span class="price price-mid" style="font-size:15px;">${esc(issue.price_mid)}</span>` : ""}
        ${issue.price_low && issue.price_high ? `<span style="font-size:11px;color:var(--muted);font-family:var(--font-cond);">${esc(issue.price_low)} – ${esc(issue.price_high)}</span>` : ""}
      </div>
    </div>
  `;
}

// ══════════════════════════════════════════════════════
// MODAL
// ══════════════════════════════════════════════════════

function openModal(issue) {
  const backdrop = document.getElementById("modalBackdrop");
  const content = document.getElementById("modalContent");
  const hasVariants = issue.variants && issue.variants.length > 0;

  content.innerHTML = `
    <div class="modal-hero">
      <div class="modal-cover-wrap">
        ${
          issue.cover_image
            ? `<img class="modal-cover" src="${esc(issue.cover_image)}" alt="${esc(issue.title)}">`
            : `<div style="width:120px;height:180px;background:var(--panel3);border-radius:4px;display:flex;align-items:center;justify-content:center;">
                 <span style="font-family:var(--font-display);font-size:40px;color:var(--panel2);">#</span>
               </div>`
        }
      </div>
      <div class="modal-headline">
        <div class="modal-issue-num">${esc(issue.publisher)} · ${esc(issue.year)}${issue.volume ? " · " + esc(issue.volume) : ""}</div>
        <div class="modal-title">${esc(issue.title)}</div>
        ${issue.is_key ? `<span class="modal-key-badge">★ ${esc(issue.key_badge || "KEY ISSUE")}</span>` : ""}
        ${
          issue.price_low || issue.price_mid || issue.price_high
            ? `<div class="modal-prices">
                 ${issue.price_low ? `<div class="modal-price-item"><span class="modal-price-label">Low</span><span class="modal-price-val low">${esc(issue.price_low)}</span></div>` : ""}
                 ${issue.price_mid ? `<div class="modal-price-item"><span class="modal-price-label">Mid</span><span class="modal-price-val mid">${esc(issue.price_mid)}</span></div>` : ""}
                 ${issue.price_high ? `<div class="modal-price-item"><span class="modal-price-label">High</span><span class="modal-price-val high">${esc(issue.price_high)}</span></div>` : ""}
               </div>`
            : ""
        }
      </div>
    </div>
    <div class="modal-body">
      ${
        issue.key_notes && issue.key_notes.length > 0
          ? `<div class="modal-section-title">Key Notes</div>
             ${issue.key_notes.map((n) => `<div class="key-note-item">${esc(n)}</div>`).join("")}
             <div style="margin-bottom:1rem;"></div>`
          : ""
      }
      ${
        issue.tags && issue.tags.length > 0
          ? `<div class="modal-section-title">Tags</div>
             <div class="modal-tags">
               ${issue.tags.map((t) => `<span class="tag" style="font-size:12px;padding:3px 8px;">${esc(t)}</span>`).join("")}
             </div>`
          : ""
      }
      ${
        issue.detail_url
          ? `<a class="modal-link" href="${esc(issue.detail_url)}" target="_blank" rel="noopener">
               <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
               View on Key Collector
             </a>`
          : ""
      }
      ${
        hasVariants
          ? `<div style="margin-top:1.25rem;">
               <div class="modal-section-title">Variants (${issue.variants.length})</div>
               <div class="variants-grid">
                 ${issue.variants
                   .map(
                     (v) => `
                       <div class="variant-card">
                         ${
                           v.cover_image
                             ? `<img class="variant-cover" src="${esc(v.cover_image)}" alt="" loading="lazy">`
                             : `<div style="width:100%;aspect-ratio:2/3;background:var(--panel3);display:flex;align-items:center;justify-content:center;">
                                  <span style="font-family:var(--font-display);font-size:24px;color:var(--panel2);">#</span>
                                </div>`
                         }
                         <div class="variant-info">
                           <div class="variant-title">${esc(v.title)}</div>
                           ${v.price_mid ? `<div class="variant-price">${esc(v.price_mid)}</div>` : ""}
                           ${v.tags && v.tags.length ? `<div class="tag-row" style="margin-top:3px;">${v.tags.map((t) => `<span class="tag" style="font-size:10px;">${esc(t)}</span>`).join("")}</div>` : ""}
                         </div>
                       </div>
                     `,
                   )
                   .join("")}
               </div>
             </div>`
          : ""
      }
    </div>
  `;

  backdrop.classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeModal(e) {
  if (e.target === document.getElementById("modalBackdrop")) closeModalDirect();
}

function closeModalDirect() {
  document.getElementById("modalBackdrop").classList.remove("open");
  document.body.style.overflow = "";
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModalDirect();
});

// ══════════════════════════════════════════════════════
// VIEW / FILTER CONTROLS
// ══════════════════════════════════════════════════════

function setView(v) {
  state.view = v;
  renderIssues();
}

function toggleKeyFilter() {
  state.keyOnly = !state.keyOnly;
  document.getElementById("keyToggle").classList.toggle("on", state.keyOnly);
  renderIssues();
}

function toggleVariantFilter() {
  state.variantOnly = !state.variantOnly;
  document
    .getElementById("variantToggle")
    .classList.toggle("on", state.variantOnly);
  renderIssues();
}

// ══════════════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════════════

function esc(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function parseMoney(str) {
  if (!str) return 0;
  return parseFloat(str.replace(/[^0-9.]/g, "")) || 0;
}
