"""Visual building blocks for the Streamlit UI (app.py): CSS + HTML snippets.

Pure functions that return strings, so they can be unit tested without
Streamlit. Charts are hand-drawn SVG because st.line_chart needs pandas, whose
DLLs Windows Smart App Control can block.
"""
from __future__ import annotations

import html
from typing import Any
from urllib.parse import urlparse

ACCENT = "#c4502b"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --bg:#f6f1e8; --surface:#fbf8f2; --surface-2:#f1ebe0; --line:#e4dccd;
  --ink:#1d1c1a; --ink-2:#4a463f; --muted:#7a7468;
  --accent:#c4502b; --accent-soft:#f6e1d7;
  --good:#2f7a4c; --good-soft:#e2f0e6; --bad:#b03f2b; --bad-soft:#f8e0d9;
  --navy:#121826; --navy-2:#1b2333; --navy-ink:#e9e5dc; --navy-muted:#8b93a3;
  --serif:'Newsreader', Georgia, serif;
  --sans:'Inter', system-ui, sans-serif;
  --mono:'JetBrains Mono', ui-monospace, monospace;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"]{background:var(--bg)!important;color:var(--ink);font-family:var(--sans);}
[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:2.2rem;max-width:1280px;}
h1,h2,h3{font-family:var(--serif)!important;font-weight:400!important;letter-spacing:-.02em;}
[data-testid="stToolbar"],[data-testid="stAppDeployButton"]{display:none!important;}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:var(--navy)!important;}
[data-testid="stSidebar"] *{color:var(--navy-ink);}
[data-testid="stSidebar"] .stButton button{
  width:100%;justify-content:flex-start;background:transparent;border:1px solid transparent;
  color:var(--navy-muted);font-size:15px;padding:.45rem .7rem;border-radius:10px;}
[data-testid="stSidebar"] .stButton button > div{width:100%;display:flex;justify-content:flex-start;gap:10px;}
[data-testid="stSidebar"] .stButton button p{text-align:left;}
[data-testid="stSidebar"] .stButton button:hover{background:var(--navy-2);color:var(--navy-ink);border-color:transparent;}
[data-testid="stSidebar"] .st-key-new_research button{
  border:1px solid #2c3546;color:var(--navy-ink);justify-content:space-between;font-weight:500;}
[data-testid="stSidebar"] [class*="st-key-navon_"] button{background:var(--navy-2);color:var(--navy-ink);}
[data-testid="stSidebar"] [data-testid="stExpander"] details{background:var(--navy-2);border:1px solid #2c3546;border-radius:10px;}
.brand{font-family:var(--serif);font-style:italic;font-size:30px;line-height:1;color:var(--navy-ink);}
.brand small{font-family:var(--mono);font-style:normal;font-size:11px;letter-spacing:.16em;color:var(--navy-muted);margin-left:8px;}
.side-label{font-family:var(--mono);font-size:11px;letter-spacing:.16em;color:var(--navy-muted);margin:18px 0 6px;}
.recent{padding:8px 10px;border-radius:10px;margin-bottom:2px;}
.recent b{display:block;font-weight:500;font-size:14.5px;color:var(--navy-ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.recent span{font-family:var(--mono);font-size:11px;color:var(--navy-muted);}
.recent.on{background:var(--navy-2);}
.status{font-family:var(--mono);font-size:12px;color:var(--navy-muted);margin-top:18px;padding-top:12px;border-top:1px solid #222b3b;}
.status i{display:inline-block;width:7px;height:7px;border-radius:50%;background:#3fb46b;margin-right:8px;}
.status b{color:var(--navy-ink);font-weight:500;}

/* ---------- shared ---------- */
.eyebrow{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;color:var(--muted);text-transform:uppercase;}
.thread-head{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:18px;}
.thread-head h2{font-size:34px;margin:2px 0 0;line-height:1.1;}
.meta{font-family:var(--mono);font-size:12.5px;color:var(--muted);white-space:nowrap;}
.stButton button{border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--ink-2);}
.stButton button:hover{border-color:var(--accent);color:var(--accent);}
[class*="st-key-try"] .stButton button{text-align:left;justify-content:flex-start;padding:.55rem 1rem;font-size:15px;}

/* version switch */
.st-key-version_switch button{font-family:var(--mono);font-size:13px;padding:.3rem .9rem;border-radius:999px!important;margin-right:6px;border:1px solid var(--line)!important;background:var(--surface);}
.st-key-version_switch button[aria-checked="true"],.st-key-version_switch button[kind*="Active"]{background:var(--accent)!important;color:#fff!important;border-color:var(--accent)!important;}
.st-key-version_switch [data-testid="stButtonGroup"]{gap:6px;flex-wrap:wrap;}

/* chat */
[data-testid="stChatMessage"]{background:transparent;padding:.4rem 0;}
[data-testid="stChatMessageContent"]{font-size:16px;line-height:1.65;}
[data-testid="stExpander"] details{background:var(--surface-2);border:1px solid var(--line);border-radius:12px;}
[data-testid="stExpander"] summary{font-family:var(--mono);font-size:13px;color:var(--ink-2);}
[data-testid="stChatInput"]{border-radius:18px;}
[data-testid="stChatInput"] > div{border-radius:18px;background:var(--surface);border:1px solid var(--line);}
[data-testid="stChatInputSubmitButton"]{background:var(--accent)!important;border-radius:50%!important;color:#fff!important;}
[data-testid="stBottom"] > div{background:var(--bg);}

/* sources */
.src-panel{position:sticky;top:1rem;}
.src{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.src .top{display:flex;align-items:center;gap:10px;margin-bottom:8px;}
.src .n{font-family:var(--mono);font-size:12px;background:var(--accent-soft);color:var(--accent);border-radius:6px;padding:1px 7px;}
.src .d{font-family:var(--mono);font-size:12.5px;color:var(--ink-2);}
.src a{color:var(--ink);text-decoration:none;font-weight:500;font-size:15.5px;line-height:1.35;}
.src a:hover{color:var(--accent);}
.src p{color:var(--muted);font-size:13.5px;margin:6px 0 0;line-height:1.5;}
.src-empty{color:var(--muted);font-size:14px;border:1px dashed var(--line);border-radius:14px;padding:16px;}

/* evals */
.hero h1{font-size:62px;line-height:1.05;margin:.3rem 0 .5rem;letter-spacing:-.03em;}
.hero h1 em{color:var(--accent);font-style:italic;}
.hero p{color:var(--ink-2);font-size:18px;margin:0;}
.timeline{display:flex;justify-content:space-between;position:relative;margin:34px 6px 30px;}
.timeline:before{content:"";position:absolute;left:6%;right:6%;top:15px;height:2px;background:var(--accent);opacity:.75;}
.tl{flex:1;text-align:center;position:relative;}
.tl .dot{width:30px;height:30px;margin:0 auto 10px;border-radius:50%;background:var(--surface);border:2px solid var(--accent);display:flex;align-items:center;justify-content:center;}
.tl .dot i{width:12px;height:12px;border-radius:50%;background:#9aa1ab;}
.tl.on .dot i{background:var(--accent);}
.tl .v{font-family:var(--mono);font-size:12.5px;color:var(--muted);}
.tl.on .v{color:var(--accent);}
.tl .name{font-size:15.5px;color:var(--ink);margin-top:2px;}
.cards{display:grid;grid-template-columns:repeat(6,1fr);background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden;}
.card{padding:18px 18px 16px;border-right:1px solid var(--line);}
.card:last-child{border-right:none;}
.card .lbl{font-size:14px;color:var(--ink-2);}
.card .val{font-family:var(--serif);font-size:44px;line-height:1.1;margin:12px 0 10px;}
.badge{display:inline-block;font-family:var(--mono);font-size:12.5px;border-radius:6px;padding:2px 8px;}
.badge.up{background:var(--good-soft);color:var(--good);}
.badge.down{background:var(--bad-soft);color:var(--bad);}
.badge.flat{background:var(--surface-2);color:var(--muted);}
.card .was{font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:10px;}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px 22px;}
.panel h3{font-size:30px;margin:0 0 4px;}
.panel .sub{color:var(--ink-2);margin-bottom:14px;}
.rel{border-top:1px solid var(--line);padding:14px 0;}
.rel:first-of-type{border-top:none;}
.rel .row{display:flex;justify-content:space-between;align-items:center;gap:10px;}
.rel .t{font-size:16px;color:var(--ink);}
.rel .t span{font-family:var(--mono);font-size:13px;color:var(--muted);margin-right:6px;}
.rel .d{color:var(--ink-2);font-size:14px;margin:4px 0 8px;}
.chip{display:inline-block;font-family:var(--mono);font-size:11.5px;background:var(--surface-2);border:1px solid var(--line);border-radius:6px;padding:2px 7px;margin:0 6px 6px 0;color:var(--ink-2);}
.rel details summary{font-size:12.5px;color:var(--muted);cursor:pointer;}
.rel details p{font-size:13px;color:var(--ink-2);margin:6px 0 0;}
.matrix{width:100%;border-collapse:collapse;font-size:14px;}
.matrix th{font-family:var(--mono);font-weight:400;font-size:12px;color:var(--muted);text-align:center;padding:8px;border-bottom:1px solid var(--line);}
.matrix th:first-child,.matrix td:first-child{text-align:left;}
.matrix td{padding:8px;border-bottom:1px solid var(--line);text-align:center;}
.matrix td:first-child{font-family:var(--mono);font-size:12.5px;color:var(--ink-2);}
.ok{color:var(--good);font-weight:600;} .ko{color:var(--bad);font-weight:600;} .na{color:var(--muted);}
.calls{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px;}
.calls td{padding:6px 8px;border-top:1px solid var(--line);vertical-align:top;}
.calls td:nth-child(3){font-family:var(--mono);font-size:12px;color:var(--ink-2);word-break:break-word;}
.watch{color:var(--ink-2);font-size:14px;margin:4px 0 6px;}
.prompt-q{font-size:16px;color:var(--ink);}
@media (max-width:1100px){.cards{grid-template-columns:repeat(3,1fr);} .card:nth-child(3){border-right:none;} .hero h1{font-size:46px;}}
</style>
"""


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def delta_badge(new: float | None, old: float | None) -> str:
    if new is None or old is None:
        return '<span class="badge flat">—</span>'
    diff = (new - old) * 100
    if abs(diff) < 0.05:
        return '<span class="badge flat">= 0 pts</span>'
    cls, arrow = ("up", "↗") if diff > 0 else ("down", "↘")
    return f'<span class="badge {cls}">{arrow} {diff:+.1f} pts</span>'


def brand_html(name: str = "Research", tag: str = "Agent") -> str:
    return f'<div class="brand">{esc(name)}<small>{esc(tag.upper())}</small></div>'


def recent_html(items: list[dict[str, str]], current: str | None) -> str:
    if not items:
        return '<div class="recent"><span>Chưa có hội thoại</span></div>'
    rows = []
    for item in items:
        on = " on" if current and item["id"] == current else ""
        rows.append(f'<div class="recent{on}"><b>{esc(item["title"])}</b><span>{esc(item["when"])}</span></div>')
    return "".join(rows)


def status_html(version: str, name: str) -> str:
    return f'<div class="status"><i></i>Running <b>{esc(version)}</b> · <b>{esc(name)}</b></div>'


def thread_head_html(title: str, n_turns: int, n_sources: int) -> str:
    return (
        '<div class="thread-head"><div><div class="eyebrow">Thread</div>'
        f'<h2>{esc(title)}</h2></div>'
        f'<div class="meta">{n_turns} lượt · {n_sources} nguồn</div></div>'
    )


def _domain(url: str | None) -> str:
    if not url:
        return ""
    host = urlparse(url).netloc
    return host[4:] if host.startswith("www.") else host


def _snippet(item: dict[str, Any]) -> str:
    for key in ("summary", "snippet", "content", "text", "description"):
        if isinstance(item.get(key), str) and item[key].strip():
            text = " ".join(item[key].split())
            return text[:160] + ("…" if len(text) > 160 else "")
    parts = []
    if item.get("points") is not None:
        parts.append(f"{item['points']} điểm · {item.get('num_comments') or 0} bình luận")
    if item.get("cited_by_count") is not None:
        parts.append(f"{item['cited_by_count']:,} trích dẫn")
    if item.get("publication_year"):
        parts.append(str(item["publication_year"]))
    if item.get("stars") is not None:
        parts.append(f"★ {item['stars']:,}")
    return " · ".join(parts)


def collect_sources(turns: list[dict[str, Any]], limit: int = 12) -> list[dict[str, str]]:
    """Unique items with a title or URL from every tool result in the thread."""
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for turn in turns:
        for rnd in turn.get("rounds") or []:
            for event in rnd.get("tool_results") or []:
                result = event.get("result")
                items = result.get("items") if isinstance(result, dict) else None
                for item in items or []:
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url") or item.get("hn_url") or ""
                    title = item.get("title") or item.get("name") or url
                    key = url or title
                    if not title or key in seen:
                        continue
                    seen.add(key)
                    sources.append({
                        "title": str(title),
                        "url": str(url),
                        "domain": item.get("source") or _domain(url) or str(event.get("tool") or ""),
                        "snippet": _snippet(item),
                        "tool": str(event.get("tool") or ""),
                    })
                    if len(sources) >= limit:
                        return sources
    return sources


def sources_html(sources: list[dict[str, str]]) -> str:
    head = '<div class="src-panel"><div class="eyebrow">Evidence</div><h3 style="font-size:28px;margin:2px 0 14px">Sources</h3>'
    if not sources:
        return head + '<div class="src-empty">Nguồn từ kết quả tool (web, HN, arXiv, OpenAlex…) sẽ hiện ở đây.</div></div>'
    cards = []
    for i, src in enumerate(sources, 1):
        title = esc(src["title"])
        link = f'<a href="{esc(src["url"])}" target="_blank">{title}</a>' if src["url"] else f"<a>{title}</a>"
        snippet = f'<p>{esc(src["snippet"])}</p>' if src["snippet"] else ""
        cards.append(
            f'<div class="src"><div class="top"><span class="n">{i}</span><span class="d">{esc(src["domain"])}</span></div>'
            f"{link}{snippet}</div>"
        )
    return head + "".join(cards) + "</div>"


def hero_html(n_cases: int, model: str, date: str, n_versions: int) -> str:
    return (
        f'<div class="hero"><div class="eyebrow">Evaluation · {n_cases} case · {esc(model)} · {esc(date)}</div>'
        '<h1>Agent đã <em>tốt lên</em> thế nào</h1>'
        f'<p>{n_versions} version trên cùng bộ eval. Chọn hai version để xem chính xác điều gì thay đổi.</p></div>'
    )


def timeline_html(versions: list[dict[str, str]], start: str, end: str) -> str:
    order = [v["version"] for v in versions]
    lo, hi = (order.index(start), order.index(end)) if start in order and end in order else (0, len(order) - 1)
    lo, hi = min(lo, hi), max(lo, hi)
    cells = []
    for i, v in enumerate(versions):
        on = " on" if i in (lo, hi) else ""
        when = f' · {esc(v["when"])}' if v.get("when") else ""
        cells.append(
            f'<div class="tl{on}"><div class="dot"><i></i></div>'
            f'<div class="v">{esc(v["version"])}{when}</div><div class="name">{esc(v["name"])}</div></div>'
        )
    return f'<div class="timeline">{"".join(cells)}</div>'


def metric_cards_html(cards: list[dict[str, Any]]) -> str:
    out = []
    for card in cards:
        new, old = card.get("new"), card.get("old")
        value = card.get("display") or pct(new)
        was = card.get("was") or pct(old)
        out.append(
            f'<div class="card"><div class="lbl">{esc(card["label"])}</div>'
            f'<div class="val">{esc(value)}</div>{delta_badge(new, old)}'
            f'<div class="was">was {esc(was)}</div></div>'
        )
    return f'<div class="cards">{"".join(out)}</div>'


def trend_svg(points: list[tuple[str, float | None]], *, start: str | None = None, end: str | None = None,
              width: int = 640, height: int = 260) -> str:
    """Single-series line chart, y axis 50%–100% (all scores live there).

    Points with value None are skipped (e.g. a suite that was not run for that version).
    The selected From→To range is shaded. <title> elements give hover tooltips.
    """
    left, right, top, bottom = 48, 16, 28, 34
    plot_w, plot_h = width - left - right, height - top - bottom
    n = max(len(points), 1)
    lo_y = 0.5

    def x(i: int) -> float:
        return left + (plot_w * i / (n - 1) if n > 1 else plot_w / 2)

    def y(v: float) -> float:
        return top + plot_h * (1 - (max(v, lo_y) - lo_y) / (1 - lo_y))

    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Trend across versions" '
             f'style="font-family:JetBrains Mono,monospace;font-size:11px">']
    names = [p[0] for p in points]
    if start in names and end in names:
        a, b = sorted((names.index(start), names.index(end)))
        parts.append(f'<rect x="{x(a):.1f}" y="{top}" width="{max(x(b) - x(a), 2):.1f}" height="{plot_h}" '
                     f'fill="{ACCENT}" fill-opacity="0.07"/>')
    for g in (0.5, 0.75, 1.0):
        gy = y(g)
        parts.append(f'<line x1="{left}" x2="{width - right}" y1="{gy:.1f}" y2="{gy:.1f}" stroke="#e4dccd" stroke-width="1"/>')
        parts.append(f'<text x="{left - 8}" y="{gy + 4:.1f}" text-anchor="end" fill="#7a7468">{g * 100:.0f}%</text>')
    for i, name in enumerate(names):
        parts.append(f'<text x="{x(i):.1f}" y="{height - 10}" text-anchor="middle" fill="#7a7468">{esc(name)}</text>')
    coords = [(x(i), y(v), name, v) for i, (name, v) in enumerate(points) if v is not None]
    if len(coords) > 1:
        path = " ".join(f"{'M' if k == 0 else 'L'}{cx:.1f},{cy:.1f}" for k, (cx, cy, _, _) in enumerate(coords))
        parts.append(f'<path d="{path}" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linejoin="round"/>')
    for cx, cy, name, v in coords:
        parts.append(
            f'<g><circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="transparent"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="#fbf8f2" stroke="{ACCENT}" stroke-width="2"/>'
            f'<title>{esc(name)}: {v * 100:.1f}%</title></g>'
        )
    if coords:
        cx, cy, _, v = coords[-1]
        parts.append(f'<text x="{cx - 8:.1f}" y="{cy - 12:.1f}" text-anchor="end" fill="#1d1c1a">{v * 100:.0f}%</text>')
    parts.append("</svg>")
    return "".join(parts)


def releases_html(releases: list[dict[str, Any]], start: str, end: str) -> str:
    head = (f'<div class="panel"><h3>What changed</h3>'
            f'<div class="sub">{esc(start)} → {esc(end)}: {len(releases)} release</div>')
    if not releases:
        return head + '<div class="sub">Chọn hai version khác nhau để xem thay đổi.</div></div>'
    rows = []
    for rel in releases:
        chips = "".join(f'<span class="chip">{esc(c)}</span>' for c in rel.get("chips", []))
        detail = (f'<details><summary>Giả thuyết đầy đủ</summary><p>{esc(rel["hypothesis"])}</p></details>'
                  if rel.get("hypothesis") else "")
        rows.append(
            f'<div class="rel"><div class="row"><div class="t"><span>{esc(rel["version"])}</span>{esc(rel["name"])}</div>'
            f'{delta_badge(rel.get("after"), rel.get("before"))}</div>'
            f'<div class="d">{esc(rel.get("summary", ""))}</div>{chips}{detail}</div>'
        )
    return head + "".join(rows) + "</div>"


def matrix_html(rows: list[dict[str, str]]) -> str:
    if not rows:
        return '<div class="sub">Mọi case đều pass ở mọi version đã chạy.</div>'
    headers = list(rows[0])
    marks = {"✅": '<span class="ok">✓</span>', "❌": '<span class="ko">✗</span>', "—": '<span class="na">—</span>'}
    out = ['<table class="matrix"><tr>', *(f"<th>{esc(h)}</th>" for h in headers), "</tr>"]
    for row in rows:
        out.append("<tr>")
        for h in headers:
            value = row.get(h, "")
            out.append(f"<td>{marks.get(value, esc(value))}</td>")
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def calls_html(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    out = ['<table class="calls">']
    for row in rows:
        ok = row.get("Kết quả", "").startswith("✅")
        mark = '<span class="ok">✓</span>' if ok else '<span class="ko">✗</span>'
        out.append(
            f'<tr><td style="width:44px;font-family:var(--mono)">{esc(row.get("Version"))}</td>'
            f'<td style="width:22px">{mark}</td><td>{esc(row.get("Tool calls thật"))}</td></tr>'
        )
    out.append("</table>")
    return "".join(out)
