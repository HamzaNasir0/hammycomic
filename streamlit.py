import asyncio
import json
import re
import threading
import queue
from urllib.parse import urljoin, quote_plus

import aiohttp
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd

# ─── Config ───────────────────────────────────────────────────────────────────

BASE = "https://www.keycollectorcomics.com"
CONNECTION_LIMIT = 10

st.set_page_config(
    page_title="Key Collector Comics Scraper",
    page_icon="📚",
    layout="wide",
)

# ─── Styling ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

:root {
    --bg: #0d0d0f;
    --surface: #15151a;
    --surface2: #1c1c24;
    --border: #2a2a36;
    --amber: #f59e0b;
    --amber-dim: #78490a;
    --green: #22c55e;
    --red: #ef4444;
    --cyan: #22d3ee;
    --text: #e2e2e8;
    --muted: #6b6b80;
}

html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

.stApp { background: var(--bg) !important; }

h1 {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 3.5rem !important;
    letter-spacing: 0.06em !important;
    color: var(--amber) !important;
    line-height: 1 !important;
    margin-bottom: 0 !important;
}

h2, h3 {
    font-family: 'Bebas Neue', sans-serif !important;
    color: var(--amber) !important;
    letter-spacing: 0.05em !important;
}

.subtitle {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: -0.25rem;
    margin-bottom: 2rem;
}

/* Input */
div[data-testid="stTextInput"] input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px rgba(245,158,11,0.15) !important;
}

/* Buttons */
.stButton > button {
    background: var(--amber) !important;
    color: #0d0d0f !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.08em !important;
    padding: 0.6rem 2rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #fbbf24 !important;
    transform: translateY(-1px) !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    padding: 1rem !important;
}
[data-testid="metric-container"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2rem !important;
    color: var(--amber) !important;
}

/* Log box */
.log-box {
    background: #0a0a0c;
    border: 1px solid var(--border);
    border-left: 3px solid var(--amber);
    padding: 1rem 1.25rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    line-height: 1.7;
    max-height: 280px;
    overflow-y: auto;
    color: var(--muted);
}
.log-info  { color: var(--cyan); }
.log-ok    { color: var(--green); }
.log-warn  { color: var(--amber); }
.log-error { color: var(--red); }

/* Dataframe / table */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    color: var(--text) !important;
}

/* Tag pill */
.tag-pill {
    display: inline-block;
    background: rgba(245,158,11,0.12);
    border: 1px solid var(--amber-dim);
    color: var(--amber);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    padding: 0.1rem 0.5rem;
    margin: 0.1rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Key badge */
.key-badge {
    display: inline-block;
    background: var(--amber);
    color: #0d0d0f;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.8rem;
    padding: 0.1rem 0.5rem;
    letter-spacing: 0.06em;
}

/* Section divider */
.section-rule {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.5rem 0;
}

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: transparent !important;
    border: 1px solid var(--amber) !important;
    color: var(--amber) !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1rem !important;
    letter-spacing: 0.08em !important;
    border-radius: 0 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(245,158,11,0.1) !important;
}

/* Progress */
.stProgress > div > div > div {
    background: var(--amber) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Scraper core ─────────────────────────────────────────────────────────────

def text_one(parent, selector, default=""):
    el = parent.select_one(selector)
    return el.get_text(strip=True) if el else default


def parse_int(text):
    text = text.replace(",", "").strip()
    return int(text) if text.isdigit() else 0


async def fetch(session, url):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.text()


def get_total_pages(soup):
    links = soup.select("nav.pagination-container a")
    if not links:
        return 1
    last_href = links[-1].get("href", "")
    match = re.search(r"page=(\d+)", last_href)
    return int(match.group(1)) if match else 1


def read_series_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("a.group.flex-col")
    results = []
    for card in cards:
        title_text = text_one(card, "h3", "Unknown Series")
        publisher = text_one(card, "span.text-primary")
        dates = text_one(card, "p.text-gray-500")
        key_count = parse_int(text_one(card, "span.border-amber-200 span", "0"))
        total_count = parse_int(text_one(card, "span.bg-gray-50 span", "0"))
        url = urljoin(BASE, card.get("href", ""))
        results.append({
            "title": title_text,
            "publisher": publisher,
            "dates": dates,
            "key_issues": key_count,
            "total_issues": total_count,
            "url": url,
            "issues": [],
        })
    return results


def read_issue_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.issue-card")
    issues = []
    for card in cards:
        card_classes = card.get("class", [])
        is_key = "isKey" in card_classes
        issue_title = text_one(card, "h2", "Unknown Issue")
        key_badge = text_one(card, "div.text-xs.whitespace-nowrap")
        meta_parts = []
        for span in card.select("div.flex.items-center.flex-wrap.text-sm.text-gray-500 span"):
            t = span.get_text(strip=True)
            if t and t != "•":
                meta_parts.append(t)
        meta_parts = list(dict.fromkeys(meta_parts))
        publisher = meta_parts[0] if len(meta_parts) > 0 else ""
        year = meta_parts[1] if len(meta_parts) > 1 else ""
        volume = meta_parts[2] if len(meta_parts) > 2 else ""
        img = card.select_one("img.border-4.border-white.rounded")
        cover_img = img.get("src", "") if img else ""
        detail_url = ""
        for a in card.select("a"):
            if "View Details" in a.get_text(" ", strip=True):
                detail_url = urljoin(BASE, a.get("href", ""))
                break
        price_low = text_one(card, "div.kc-price-low .currency")
        price_mid = text_one(card, "div.kc-price-mid .currency")
        price_high = text_one(card, "div.kc-price-high .currency")
        notes = list(dict.fromkeys([
            el.get_text(strip=True)
            for el in card.select("div.border-\\[\\#E0C2FF\\] h3")
            if el.get_text(strip=True)
        ]))
        tags = list(dict.fromkeys([
            el.get_text(strip=True)
            for el in card.select("span.bg-primary\\/10")
            if el.get_text(strip=True)
        ]))
        variant_url = ""
        variant_count = 0
        for a in card.select("a"):
            link_text = a.get_text(" ", strip=True)
            if "View Variants" in link_text:
                m = re.search(r"\((\d+)\)", link_text)
                if m and int(m.group(1)) > 1:
                    variant_count = int(m.group(1))
                    variant_url = urljoin(BASE, a.get("href", ""))
                break
        has_variants = variant_count > 1 and bool(variant_url)
        issues.append({
            "title": issue_title,
            "publisher": publisher,
            "year": year,
            "volume": volume,
            "is_key": is_key,
            "key_badge": key_badge,
            "cover_image": cover_img,
            "detail_url": detail_url,
            "price_low": price_low,
            "price_mid": price_mid,
            "price_high": price_high,
            "key_notes": notes,
            "tags": tags,
            "has_variants": has_variants,
            "variant_count": variant_count,
            "variant_url": variant_url,
            "variants": [],
        })
    return issues


async def scrape_series(session, series_url, log_q):
    html = await fetch(session, series_url)
    soup = BeautifulSoup(html, "html.parser")
    total_pages = get_total_pages(soup)
    log_q.put(("info", f"  Series pages: {total_pages}"))

    page_urls = [
        series_url if p == 1 else f"{series_url.rstrip('/')}/?page={p}"
        for p in range(1, total_pages + 1)
    ]

    async def scrape_issue_page(page_url, page_num):
        log_q.put(("info", f"    Page {page_num}/{total_pages} – reading issues…"))
        html = await fetch(session, page_url)
        issues = read_issue_cards(html)

        variant_tasks = [
            scrape_variants(idx, issue["variant_url"])
            for idx, issue in enumerate(issues)
            if issue["has_variants"] and issue["variant_url"]
        ]
        variant_results = await asyncio.gather(*variant_tasks, return_exceptions=True)
        for result in variant_results:
            if isinstance(result, Exception):
                log_q.put(("error", f"    Variant error: {result}"))
                continue
            idx, variant_issues = result
            issues[idx]["variants"] = variant_issues

        log_q.put(("ok", f"    Page {page_num} done – {len(issues)} issues"))
        return issues

    async def scrape_variants(idx, variant_url):
        log_q.put(("warn", f"    → Variants: {variant_url}"))
        variant_html = await fetch(session, variant_url)
        return idx, read_issue_cards(variant_html)

    results = await asyncio.gather(*[scrape_issue_page(u, i + 1) for i, u in enumerate(page_urls)], return_exceptions=True)
    all_issues = []
    for result in results:
        if isinstance(result, Exception):
            log_q.put(("error", f"  Issue page failed: {result}"))
            continue
        all_issues.extend(result)
    return all_issues


async def scrape_comic_info(search_query, log_q, result_q):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0"
        )
    }
    timeout = aiohttp.ClientTimeout(total=60)
    connector = aiohttp.TCPConnector(limit=CONNECTION_LIMIT)
    all_series = []

    async with aiohttp.ClientSession(headers=headers, timeout=timeout, connector=connector) as session:
        query = quote_plus(search_query)
        base_url = f"{BASE}/series/?search={query}&groupBy=series&orderBy=queryRelevance"
        log_q.put(("info", f"Searching: {base_url}"))

        html = await fetch(session, base_url)
        soup = BeautifulSoup(html, "html.parser")
        total_search_pages = get_total_pages(soup)
        log_q.put(("info", f"Search pages: {total_search_pages}"))

        search_page_urls = [f"{base_url}&page={sp}" for sp in range(1, total_search_pages + 1)]

        async def scrape_search_page(page_url, sp):
            log_q.put(("info", f"\n=== Search page {sp}/{total_search_pages} ==="))
            html = await fetch(session, page_url)
            series_list = read_series_cards(html)
            log_q.put(("ok", f"  Found {len(series_list)} series"))
            if not series_list:
                log_q.put(("warn", "  No series found – site may use JS rendering"))
                return []

            async def scrape_one_series(series_data, index):
                log_q.put(("info", f"  [{index + 1}/{len(series_list)}] {series_data['title']} (total={series_data['total_issues']})"))
                if series_data["total_issues"] > 0:
                    series_data["issues"] = await scrape_series(session, series_data["url"], log_q)
                return series_data

            results = await asyncio.gather(*[scrape_one_series(s, i) for i, s in enumerate(series_list)], return_exceptions=True)
            clean = []
            for result in results:
                if isinstance(result, Exception):
                    log_q.put(("error", f"  Series failed: {result}"))
                    continue
                clean.append(result)
            return clean

        search_results = await asyncio.gather(*[scrape_search_page(u, i + 1) for i, u in enumerate(search_page_urls)], return_exceptions=True)
        for result in search_results:
            if isinstance(result, Exception):
                log_q.put(("error", f"Search page failed: {result}"))
                continue
            all_series.extend(result)

    log_q.put(("ok", f"\nDone. {len(all_series)} series collected."))
    log_q.put(("__done__", all_series))
    result_q.put(all_series)


def run_scraper_thread(query, log_q, result_q):
    asyncio.run(scrape_comic_info(query, log_q, result_q))


# ─── UI ───────────────────────────────────────────────────────────────────────

st.markdown('<h1>Key Collector Comics</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Series & Issue Scraper</p>', unsafe_allow_html=True)

with st.form("search_form"):
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        query = st.text_input("Search query", placeholder="Spider-Man, Batman, X-Men…", label_visibility="collapsed")
    with col_btn:
        run = st.form_submit_button("SCRAPE", width='stretch')

if "results" not in st.session_state:
    st.session_state.results = None
if "logs" not in st.session_state:
    st.session_state.logs = []

# ─── Run scraper ──────────────────────────────────────────────────────────────

if run and query.strip():
    st.session_state.results = None
    st.session_state.logs = []

    log_q: queue.Queue = queue.Queue()
    result_q: queue.Queue = queue.Queue()

    thread = threading.Thread(target=run_scraper_thread, args=(query.strip(), log_q, result_q), daemon=True)
    thread.start()

    log_placeholder = st.empty()
    status_placeholder = st.empty()
    prog_placeholder = st.empty()

    logs = []
    done = False
    prog_val = 0.0

    while not done:
        try:
            while True:
                level, msg = log_q.get_nowait()
                if level == "__done__":
                    done = True
                    break
                logs.append((level, msg))
                log_q.task_done()
        except queue.Empty:
            pass

        html_lines = []
        for lvl, m in logs[-60:]:
            cls = {"info": "log-info", "ok": "log-ok", "warn": "log-warn", "error": "log-error"}.get(lvl, "")
            m_esc = m.replace("<", "&lt;").replace(">", "&gt;")
            html_lines.append(f'<span class="{cls}">{m_esc}</span>')
        log_placeholder.markdown(
            f'<div class="log-box">{"<br>".join(html_lines)}</div>',
            unsafe_allow_html=True
        )

        if not done:
            import time
            time.sleep(0.3)
            prog_val = min(prog_val + 0.005, 0.95)
            prog_placeholder.progress(prog_val)

    prog_placeholder.progress(1.0)
    thread.join(timeout=5)

    try:
        all_series = result_q.get_nowait()
        st.session_state.results = all_series
        st.session_state.logs = logs
    except queue.Empty:
        st.error("Scraper finished but no data returned.")

# ─── Display results ──────────────────────────────────────────────────────────

if st.session_state.results:
    data = st.session_state.results

    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

    total_issues = sum(len(s.get("issues", [])) for s in data)
    total_keys = sum(
        sum(1 for iss in s.get("issues", []) if iss.get("is_key"))
        for s in data
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Series Found", len(data))
    m2.metric("Total Issues", total_issues)
    m3.metric("Key Issues", total_keys)

    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

    st.download_button(
        label="⬇ DOWNLOAD JSON",
        data=json.dumps(data, indent=2, ensure_ascii=False),
        file_name="comics_data.json",
        mime="application/json",
    )

    flat_keys = []
    for series in data:
        for iss in series.get("issues", []):
            if iss.get("is_key"):
                flat_keys.append({
                    "Series": series["title"],
                    "Issue": iss["title"],
                    "Year": iss.get("year", ""),
                    "Publisher": iss.get("publisher", ""),
                    "Key Note": ", ".join(iss.get("key_notes", [])),
                    "Low": iss.get("price_low", ""),
                    "Mid": iss.get("price_mid", ""),
                    "High": iss.get("price_high", ""),
                    "Tags": ", ".join(iss.get("tags", [])),
                })

    if flat_keys:
        st.markdown("### 🔑 Key Issues")
        df = pd.DataFrame(flat_keys)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    st.markdown("### All Series")

    for series in data:
        issues = series.get("issues", [])
        key_cnt = sum(1 for i in issues if i.get("is_key"))
        label = f"{series['title']}  ·  {series['publisher']}  ·  {series['dates']}  ·  {key_cnt} keys / {len(issues)} issues"

        with st.expander(label):
            if not issues:
                st.markdown('<span style="color:var(--muted,#888);font-size:0.8rem">No issues scraped.</span>', unsafe_allow_html=True)
                continue

            cols = st.columns([1, 3, 1, 1, 1, 1])
            cols[0].markdown("**Cover**")
            cols[1].markdown("**Title**")
            cols[2].markdown("**Year**")
            cols[3].markdown("**Low**")
            cols[4].markdown("**Mid**")
            cols[5].markdown("**High**")

            for iss in issues:
                c0, c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 1, 1, 1])
                with c0:
                    if iss.get("cover_image"):
                        st.image(iss["cover_image"], width=60)
                with c1:
                    title_md = iss["title"]
                    if iss.get("is_key"):
                        title_md = f'<span class="key-badge">KEY</span> {title_md}'
                    if iss.get("key_badge"):
                        title_md += f' <span style="color:var(--amber,#f59e0b);font-size:0.75rem">– {iss["key_badge"]}</span>'
                    st.markdown(title_md, unsafe_allow_html=True)
                    if iss.get("key_notes"):
                        for note in iss["key_notes"]:
                            st.markdown(f'<span style="color:var(--muted,#888);font-size:0.72rem">• {note}</span>', unsafe_allow_html=True)
                    if iss.get("tags"):
                        pills = "".join(f'<span class="tag-pill">{t}</span>' for t in iss["tags"])
                        st.markdown(pills, unsafe_allow_html=True)
                c2.markdown(iss.get("year", "—"))
                c3.markdown(iss.get("price_low") or "—")
                c4.markdown(iss.get("price_mid") or "—")
                c5.markdown(iss.get("price_high") or "—")

# ─── Footer ───────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:var(--muted,#6b6b80);letter-spacing:0.12em;text-transform:uppercase;">
    made by hammy
</div>
""", unsafe_allow_html=True)