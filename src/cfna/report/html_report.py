from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cfna.analysis.metrics import GraphMetrics
from cfna.config import INPUT_UI_URL
from cfna.models import ROLE_COLORS, CaseBrief, CaseGraph

_ASSETS = Path(__file__).resolve().parent / "assets"

TEMPLATE_CREDIT = (
    "Layout based on TemplateMo 602 Graph Page "
    "(https://templatemo.com/tm-602-graph-page), free for commercial use."
)


def _load_css() -> str:
    parts: list[str] = []
    for name in ("graph-page.css", "cfna.css"):
        path = _ASSETS / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


CSS = _load_css()

NAV_JS = """
const hamburger = document.getElementById('hamburger');
const navLinksMobile = document.getElementById('navLinksMobile');
if (hamburger && navLinksMobile) {
  const mobileLinks = navLinksMobile.querySelectorAll('a');
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navLinksMobile.classList.toggle('active');
  });
  mobileLinks.forEach(link => link.addEventListener('click', () => {
    hamburger.classList.remove('active');
    navLinksMobile.classList.remove('active');
  }));
}
window.addEventListener('scroll', () => {
  const navbar = document.getElementById('navbar');
  if (navbar) navbar.classList.toggle('scrolled', window.scrollY > 50);
  if (hamburger) hamburger.classList.remove('active');
  if (navLinksMobile) navLinksMobile.classList.remove('active');
});

const sections = document.querySelectorAll('section[id]');
function updateActiveNav() {
  const scrollY = window.pageYOffset;
  sections.forEach(section => {
    const top = section.offsetTop - 120;
    if (scrollY <= top || scrollY > top + section.offsetHeight) return;
    document.querySelectorAll('.nav-links a, .nav-links-mobile a').forEach(link => {
      link.classList.toggle('active', link.getAttribute('href') === '#' + section.id);
    });
  });
}
window.addEventListener('scroll', updateActiveNav);
updateActiveNav();

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({behavior: 'smooth', block: 'start'});
  });
});

const barObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    entry.target.querySelectorAll('.bar').forEach((bar, i) => {
      setTimeout(() => { bar.style.animation = 'slideUp .5s ease-out forwards'; }, i * 80);
    });
    barObserver.unobserve(entry.target);
  });
}, {threshold: 0.3});
document.querySelectorAll('.bar-chart').forEach(chart => barObserver.observe(chart));
"""

GRAPH_JS = """
const DATA = __DATA__;
const ROLE_COLORS = __COLORS__;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function nodeLabel(id, value){
  return value.length > 24 ? value.slice(0,22)+'..' : value;
}

const nodes = new vis.DataSet(DATA.nodes.map(n => ({
  id: n.id, label: nodeLabel(n.id, n.value), title: n.title,
  color: {background: ROLE_COLORS[n.role] || '#78909c', border: '#0a0e27',
          highlight:{background:'#ffffff', border:'#0a0e27'}},
  font: {color:'#e7edf5', size:12}, border_width:1, shape:'dot',
  value: n.value_size, group: n.role, hidden:false
})));

const edges = new vis.DataSet(DATA.edges.map((e,i) => ({
  id: i, from: e.from, to: e.to, label: e.label, title: e.title,
  arrows: e.directed ? 'to' : undefined,
  color: e.color, smooth:{type:'continuous'}, width: e.width, dashes: e.dashes
})));

const container = document.getElementById('graph');
const network = new vis.Network(container, {nodes, edges}, {
  physics:{enabled:true, solver:'forceAtlas2Based',
    forceAtlas2Based:{gravitationalConstant:-62, springLength:44, springConstant:.06, damping:.42},
    stabilization:{iterations:220}},
  nodes:{scaling:{min:6, max:34}},
  edges:{smooth:{type:'continuous'}, font:{face:'Consolas', size:10, color:'#a0a0a0', strokeWidth:0}},
  interaction:{hover:true, tooltipDelay:120, navigationButtons:true, keyboard:false}
});

function neighborOf(id){
  const set = new Set([id]);
  edges.forEach(e => { if(e.from===id) set.add(e.to); if(e.to===id) set.add(e.from); });
  return set;
}

network.on('click', params => {
  const panel = document.getElementById('detail');
  if(!params.nodes.length){ panel.style.display='none'; return; }
  const id = params.nodes[0];
  const n = DATA.node_detail[id];
  if(!n){ panel.style.display='none'; return; }
  let html = '<h4>'+esc(id)+'</h4>';
  html += '<div class="kv">Role: <b>'+esc(n.role)+'</b> &nbsp; Risk: <b>'+n.risk+'/99</b> &nbsp; Tier: <b>'+(n.tier||'-')+'</b></div>';
  html += '<div class="kv">Type: <b>'+esc(n.type)+'</b> &nbsp; Mentions: <b>'+n.mentions+'</b></div>';
  if(n.in_amount || n.out_amount){
    html += '<div class="kv">Inflow: <b>Rs.'+n.in_amount.toLocaleString('en-IN')+'</b></div>';
    html += '<div class="kv">Outflow: <b>Rs.'+n.out_amount.toLocaleString('en-IN')+'</b></div>';
    html += '<div class="kv">Pass-through: <b>'+(n.pass_through*100).toFixed(0)+'%</b></div>';
  }
  if(n.labels && n.labels.length) html += '<div class="kv">Narrative labels: <b>'+esc(n.labels.join(', '))+'</b></div>';
  if(n.sources && n.sources.length) html += '<div class="kv">Sources: <b>'+esc(n.sources.join(', '))+'</b></div>';
  if(n.reasons && n.reasons.length){ html += '<div class="kv">Basis:</div><ul>'; n.reasons.forEach(r=> html += '<li>'+esc(r)+'</li>'); html += '</ul>'; }
  if(n.neighbors && n.neighbors.length){ html += '<div class="kv">Links ('+n.neighbors.length+'):</div><ul>'; n.neighbors.slice(0,14).forEach(x=> html += '<li>'+esc(x)+'</li>'); html += '</ul>'; }
  panel.innerHTML = html; panel.style.display='block';
  const keep = neighborOf(id);
  nodes.forEach(nd => nodes.update({id: nd.id, opacity: keep.has(nd.id) ? 1 : 0.15}));
});

let activeRoles = new Set(Object.keys(ROLE_COLORS));
document.querySelectorAll('button.filter[data-role]').forEach(btn => {
  btn.addEventListener('click', () => {
    const role = btn.dataset.role;
    if(activeRoles.has(role) && activeRoles.size === Object.keys(ROLE_COLORS).length){
      activeRoles = new Set([role]);
    } else if(activeRoles.has(role)){
      activeRoles.delete(role);
      if(!activeRoles.size) activeRoles = new Set(Object.keys(ROLE_COLORS));
    } else {
      activeRoles.add(role);
    }
    document.querySelectorAll('button.filter[data-role]').forEach(
      b => b.classList.toggle('on', activeRoles.has(b.dataset.role)));
    DATA.nodes.forEach(n => nodes.update({id:n.id, hidden: !activeRoles.has(n.role)}));
  });
});

document.getElementById('searchBtn').addEventListener('click', () => {
  const q = document.getElementById('searchInput').value.trim().toLowerCase();
  if(!q) return;
  const hit = DATA.nodes.find(n => n.value.toLowerCase().includes(q) || n.id.toLowerCase().includes(q));
  if(hit){ network.selectNodes([hit.id]); network.focus(hit.id, {scale:1.35}); network.emit('click', {nodes:[hit.id]}); }
});
document.getElementById('searchInput').addEventListener('keydown', e => {
  if(e.key==='Enter') document.getElementById('searchBtn').click();
});
document.getElementById('resetBtn').addEventListener('click', () => {
  document.getElementById('detail').style.display='none';
  nodes.forEach(nd => nodes.update({id:nd.id, opacity:1}));
  network.fit();
});
"""


def _short(node_id: str) -> str:
    return node_id.split(":", 1)[1] if ":" in node_id else node_id


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _table(headers: list[str], rows: list[list[Any]], empty: str = "none recorded") -> str:
    if not rows:
        return f'<div class="table-wrap"><p class="empty">{_esc(empty)}</p></div>'
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        cells = ""
        for cell in row:
            cls = ' class="num"' if isinstance(cell, (int, float)) and not isinstance(cell, bool) else ""
            cells += f"<td{cls}>{_esc(cell)}</td>"
        body.append(f"<tr>{cells}</tr>")
    return (
        f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )


def _bars(items: list[tuple[str, float, str]], gradient: str = "") -> str:
    """Pure-CSS bar chart in the template's `.bar-chart` markup."""
    peak = max((value for _, value, _ in items), default=0) or 1
    out = []
    for label, value, display in items:
        height = max(8, round(value / peak * 100))
        style = f"height:{height}%"
        if gradient:
            style += f";background:linear-gradient(180deg,{gradient} 0%,rgba(0,204,255,.65) 100%)"
        out.append(
            f'<div class="bar" style="{style}">'
            f'<span class="bar-value">{_esc(display)}</span>'
            f'<span class="bar-label" title="{_esc(label)}">{_esc(label)}</span></div>'
        )
    return "".join(out)


def _chart(title: str, badge: str, bars: str) -> str:
    return (
        '<div class="chart-card">'
        f'<div class="chart-header"><h3 class="chart-title">{_esc(title)}</h3>'
        f'<div class="chart-options"><span class="chart-option active">{_esc(badge)}</span></div></div>'
        f'<div class="chart-container"><div class="bar-chart">{bars}</div></div>'
        "</div>"
    )


EDGE_STYLE = {
    "transfer": {"color": {"color": "#22c55e", "highlight": "#86efac"}, "width": 2, "dashes": False, "directed": True},
    "call": {"color": {"color": "#00ccff", "highlight": "#7ce8ff"}, "width": 1.4, "dashes": True, "directed": True},
    "maps_to": {"color": {"color": "#ffcc00", "highlight": "#ffe066"}, "width": 1.2, "dashes": False, "directed": True},
    "sim_bound_to_msisdn": {"color": {"color": "#a78bfa", "highlight": "#c4b5fd"}, "width": 1.4, "dashes": False, "directed": True},
    "device_used_sim": {"color": {"color": "#ff0080", "highlight": "#ff6bb5"}, "width": 1.2, "dashes": True, "directed": True},
    "device_used_msisdn": {"color": {"color": "#ff0080", "highlight": "#ff6bb5"}, "width": 1.2, "dashes": True, "directed": True},
    "owns": {"color": {"color": "#e2e8f0", "highlight": "#ffffff"}, "width": 1.1, "dashes": False, "directed": True},
    "co_occur": {"color": {"color": "#475569", "highlight": "#94a3b8"}, "width": 0.8, "dashes": True, "directed": False},
}


def _build_graph_payload(case: CaseGraph, brief: CaseBrief, metrics: GraphMetrics) -> dict[str, Any]:
    entity_by_id = case.entities
    assessments = brief.assessments

    nodes = []
    node_detail: dict[str, Any] = {}
    relations = case.relation_list()
    for node_id, metric in metrics.nodes.items():
        ent = entity_by_id.get(node_id)
        if ent is None:
            continue
        assessment = assessments.get(node_id)
        role = assessment.role if assessment else "unknown"
        label = _short(node_id)
        neighbors = []
        for rel in relations:
            if rel.src == node_id:
                neighbors.append(
                    f"{rel.rtype} -> {_short(rel.dst)} (Rs.{rel.amount:,.0f})" if rel.amount
                    else f"{rel.rtype} -> {_short(rel.dst)}"
                )
            elif rel.dst == node_id:
                neighbors.append(
                    f"{rel.rtype} <- {_short(rel.src)} (Rs.{rel.amount:,.0f})" if rel.amount
                    else f"{rel.rtype} <- {_short(rel.src)}"
                )
        title = (
            f"{label}\ntype: {ent.etype.value}\nrole: {role}\nrisk: {assessment.risk if assessment else 0}"
            f"\nin: Rs.{metric.in_amount:,.0f}  out: Rs.{metric.out_amount:,.0f}"
        )
        nodes.append(
            {
                "id": node_id,
                "type": ent.etype.value,
                "value": label,
                "role": role,
                "title": title,
                "value_size": 4 + min(26, (metric.in_amount + metric.out_amount) ** 0.5 / 40),
            }
        )
        node_detail[node_id] = {
            "type": ent.etype.value,
            "role": role,
            "risk": assessment.risk if assessment else 0,
            "tier": assessment.tier if assessment else 0,
            "mentions": ent.mentions,
            "labels": ent.labels,
            "sources": ent.sources[:6],
            "in_amount": round(metric.in_amount, 2),
            "out_amount": round(metric.out_amount, 2),
            "pass_through": round(metric.pass_through, 3),
            "reasons": assessment.reasons if assessment else [],
            "neighbors": neighbors[:25],
        }

    max_amount = max((rel.amount for rel in relations), default=1) or 1
    edges = []
    ordered = sorted(relations, key=lambda r: (r.rtype == "co_occur", -r.amount, -r.weight))
    for rel in ordered:
        if rel.src not in metrics.nodes or rel.dst not in metrics.nodes:
            continue
        if rel.rtype == "co_occur" and len(ordered) > 600:
            continue
        style = EDGE_STYLE.get(rel.rtype, EDGE_STYLE["co_occur"])
        width = style["width"]
        if rel.rtype == "transfer":
            width = 1.2 + 4.5 * (rel.amount / max_amount) ** 0.5
        label = rel.rtype
        if rel.rtype == "transfer":
            label = (
                f"Rs.{rel.amount:,.0f}" if rel.amount < 1_00_00_000
                else f"Rs.{rel.amount / 10000000:.1f}Cr"
            )
        title = (rel.evidence[0] if rel.evidence else rel.rtype) + (f"\n{rel.first_ts}" if rel.first_ts else "")
        edges.append(
            {
                "from": rel.src,
                "to": rel.dst,
                "label": label,
                "title": title,
                "color": style["color"],
                "width": round(width, 2),
                "dashes": style["dashes"],
                "directed": style["directed"],
            }
        )
    return {"nodes": nodes, "edges": edges, "node_detail": node_detail}


NAV_LINKS = [
    ("home", "Home"),
    ("dashboard", "Dashboard"),
    ("analytics", "Analytics"),
    ("network", "Network"),
    ("hierarchy", "Hierarchy"),
    ("evidence", "Evidence"),
    ("fir", "FIR Brief"),
]


def _nav() -> str:
    def links(mobile: bool) -> str:
        out = []
        for anchor, label in NAV_LINKS:
            cls = ' class="active"' if anchor == "home" else ""
            out.append(f'<li><a href="#{anchor}"{cls}>{label}</a></li>')
        out.append(
            f'<li><a href="{INPUT_UI_URL}" target="_blank" rel="noopener">New case</a></li>'
        )
        return "".join(out)

    return f"""
<nav id="navbar">
  <div class="nav-container">
    <a href="#home" class="logo">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24"><path d="M3 13h2v8H3zm4-8h2v13H7zm4-2h2v15h-2zm4 4h2v11h-2zm4-2h2v13h-2z"/></svg>
      </div>
      <span class="logo-text">CFNA</span>
    </a>
    <ul class="nav-links">{links(False)}</ul>
    <div class="hamburger" id="hamburger"><span></span><span></span><span></span></div>
  </div>
  <ul class="nav-links-mobile" id="navLinksMobile">{links(True)}</ul>
</nav>"""


def render_html(
    case: CaseGraph,
    brief: CaseBrief,
    metrics: GraphMetrics,
    evidence: dict[str, list[dict]],
) -> str:
    meta = case.meta
    pattern = brief.primary
    stats = brief.stats
    roles = brief.hierarchy
    payload = _build_graph_payload(case, brief, metrics)
    payload["meta"] = meta.to_dict()

    data_js = json.dumps(
        {"nodes": payload["nodes"], "edges": payload["edges"],
         "node_detail": payload["node_detail"], "meta": payload["meta"]},
        ensure_ascii=False,
    )
    graph_js = GRAPH_JS.replace("__DATA__", data_js).replace("__COLORS__", json.dumps(ROLE_COLORS))
    script = NAV_JS + "\n" + graph_js

    conf = int(round(pattern.score * 100)) if pattern else 0
    role_counts = {role: len(members) for role, members in roles.items()}
    assessments = brief.assessments
    freeze_rows = [
        [r["identifier"], r["type"], r["bank"] or "-", r["upi"] or "-", f"{r['in_amount']:,.0f}",
         f"{r['out_amount']:,.0f}", r["role"], r["risk"]]
        for r in evidence.get("accounts_freeze_list", []) if r["freeze"]
    ]
    freeze_count = len(freeze_rows)
    risks = [a.risk for a in assessments.values()]
    avg_risk = round(sum(risks) / len(risks)) if risks else 0
    generated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    # ---------- hero ----------
    chips = "".join(
        [
            f'<span class="chip">Case <b>{_esc(meta.case_id)}</b></span>',
            f'<span class="chip">PS <b>{_esc(meta.police_station or "n/a")}</b></span>',
            f'<span class="chip">District <b>{_esc(meta.district or "n/a")}, {_esc(meta.state or "")}</b></span>',
            f'<span class="chip">Complainant <b>{_esc(meta.complainant or "n/a")}</b></span>',
            f'<span class="chip">Occurred <b>{_esc(meta.occurred_on or "n/a")}</b></span>',
            f'<span class="chip">Reported <b>{_esc(meta.reported_on or "n/a")}</b></span>',
            f'<span class="chip hot">Freeze list <b>{freeze_count} accounts</b></span>',
            f'<span class="chip">Generated <b>{generated}</b></span>',
        ]
    )
    verdict = (
        f"""
    <div class="verdict">
      <div class="verdict-name">{_esc(pattern.name)}</div>
      <div class="verdict-conf">{_esc(pattern.id)} &middot; {conf}% CONFIDENCE</div>
      <div class="confidence"><i style="width:{conf}%"></i></div>
      <p>{_esc(pattern.summary if pattern else "No pattern established.")}</p>
    </div>"""
        if pattern
        else '<div class="verdict"><div class="verdict-name">No pattern established</div></div>'
    )
    case_rows = [
        ("Money trail", f"Rs.{metrics.total_flow:,.0f}"),
        ("Entities / links", f"{stats.get('entities', 0)} / {stats.get('relations', 0)}"),
        ("Fraud pattern", pattern.name if pattern else "n/a"),
        ("Highest risk", f"{max(assessments, key=lambda n: assessments[n].risk) if assessments else '-'}"
                         f" ({max(risks) if risks else 0}/99)"),
        ("Mule layers", str(len({a.tier for a in assessments.values() if a.role == 'mule' and a.tier}))),
        ("Victim identifiers", str(role_counts.get("victim", 0))),
        ("Bob backend", "bob-local-rules-v1 (0 coins)"),
    ]
    case_file = (
        '<div class="case-file"><h3>Case file snapshot</h3>'
        + "".join(f'<div class="row"><span>{_esc(k)}</span><b>{_esc(v)}</b></div>' for k, v in case_rows)
        + "</div>"
    )

    # ---------- dashboard ----------
    def stat(icon: str, title: str, value: Any, desc: str, extra: str = "") -> str:
        return (
            f'<div class="stat-card{extra}">'
            f'<div class="stat-header"><div class="stat-icon">{icon}</div>'
            f'<div class="stat-title">{_esc(title)}</div></div>'
            f'<div class="stat-value">{_esc(value)}</div>'
            f'<div class="stat-description">{_esc(desc)}</div></div>'
        )

    stats_html = "".join(
        [
            stat("\U0001f4b0", "Money trail", f"Rs.{metrics.total_flow:,.0f}",
                 "Documented fraudulent volume across every loaded statement and complaint."),
            stat("\U0001f9e9", "Entities", stats.get("entities", 0),
                 "Accounts, VPAs, MSISDNs, SIMs, devices, persons and locations extracted."),
            stat("\U0001f517", "Relationships", stats.get("relations", 0),
                 "Transfers, calls, SIM bindings, device sessions and co-occurrence links."),
            stat("\U0001f465", "Victim nodes", role_counts.get("victim", 0),
                 "Identifiers that show loss-only flow and carry a victim label.", " accent-red"),
            stat("\U0001f578\ufe0f", "Mule accounts", role_counts.get("mule", 0),
                 "Pass-through nodes forwarding 85% or more of their inflow."),
            stat("\U0001f451", "Kingpins", role_counts.get("kingpin", 0),
                 "Terminal beneficiaries where the layered trail stops.", " accent-amber"),
        ]
    )

    def metric_item(value: Any, label: str) -> str:
        return f'<div class="metric-item"><div class="metric-value">{_esc(value)}</div><div class="metric-label">{_esc(label)}</div></div>'

    metrics_html = "".join(
        [
            metric_item(len(metrics.components), "Connected components"),
            metric_item(len(brief.timeline), "Timeline events"),
            metric_item(freeze_count, "Accounts to freeze"),
            metric_item(role_counts.get("operator", 0), "Operators"),
            metric_item(role_counts.get("recruiter", 0), "Recruiters"),
            metric_item(f"{avg_risk}/99", "Average risk score"),
        ]
    )

    # ---------- analytics charts ----------
    role_bars = _bars(
        [
            (role, len(members), str(len(members)))
            for role, members in roles.items() if members
        ],
        gradient="#00ffcc",
    )
    pattern_bars = _bars(
        [(p.name, p.score, f"{round(p.score * 100)}%") for p in brief.patterns[:8]],
        gradient="#ffcc00",
    )
    top_transfers = evidence.get("largest_transfers", [])[:8]
    transfer_bars = _bars(
        [
            (f"{_short(t['from'])[-6:]}->{_short(t['to'])[-6:]}", t["amount"],
             f"{t['amount']:,.0f}")
            for t in top_transfers
        ],
        gradient="#22c55e",
    )
    risk_nodes = sorted(assessments.items(), key=lambda kv: -kv[1].risk)[:8]
    risk_bars = _bars(
        [(f"{_short(n)[-8:]}", a.risk, str(a.risk)) for n, a in risk_nodes],
        gradient="#ff6b6b",
    )
    charts_html = "".join(
        [
            _chart("\U0001f4ca Role distribution", "count", role_bars or '<p class="empty">no roles</p>'),
            _chart("\U0001f50d Pattern confidence", "score", pattern_bars or '<p class="empty">no patterns</p>'),
            _chart("\U0001f4b8 Largest transfers", "Rs.", transfer_bars or '<p class="empty">no transfers</p>'),
            _chart("\U0001f6a8 Highest risk nodes", "risk/99", risk_bars or '<p class="empty">no nodes</p>'),
        ]
    )

    # ---------- network ----------
    filter_buttons = "".join(
        f'<button class="filter on" data-role="{role}">'
        f'<span style="color:{ROLE_COLORS[role]}">&#9679;</span> {role} ({role_counts.get(role, 0)})</button>'
        for role in ROLE_COLORS
    )
    legend = "".join(
        f'<span><i style="background:{color}"></i>{role}</span>' for role, color in ROLE_COLORS.items()
    )

    # ---------- hierarchy / insights ----------
    tree_lines = _tree_text(brief)
    insights = "".join(f"<li>{_esc(i)}</li>" for i in brief.insights)
    gaps = "".join(f"<li>{_esc(g)}</li>" for g in brief.gaps) or "<li>none flagged</li>"
    actions = "".join(f"<li>{_esc(a)}</li>" for a in brief.actions)
    legal = "".join(f"<li>{_esc(a)}</li>" for a in brief.legal)

    # ---------- evidence tables ----------
    victim_rows = [
        [v["identifier"], v["type"], f"{v['amount_lost']:,.0f}", ", ".join(v["paid_to"])]
        for v in evidence.get("victims", [])
    ]
    device_rows = [
        [d["imei"], d["sim_count"], d["msisdn_count"], ", ".join(d["sims"][:3]),
         ", ".join(d["msisdns"][:3]), "YES" if d["swap_signature"] else "-"]
        for d in evidence.get("devices", [])
    ]
    sim_rows = [
        [r["msisdn"], r.get("owner") or "-", r["sim_count"],
         "; ".join(f"{b['iccid']} @ {b['activation'] or b['since'] or 'n/a'}" for b in r["bindings"])]
        for r in evidence.get("sim_swap_bindings", [])
    ]
    transfer_rows = [
        [t["when"], t["from"], t["to"], f"{t['amount']:,.0f}", t["evidence"][:70]]
        for t in evidence.get("largest_transfers", [])
    ]
    timeline_rows = [
        [e.ts, e.etype, e.summary[:100]]
        for e in brief.timeline if e.etype in {"transfer", "sim_activation", "sim_event", "offence", "report"}
    ][:60]
    call_rows = [
        [c["from"], c["to"], c["count"], c["first"] or "-", c["evidence"][:60]]
        for c in evidence.get("call_records", [])
    ]

    pattern_signals = "".join(f"<li>{_esc(s)}</li>" for s in (pattern.signals if pattern else []))
    secondary = [p for p in brief.patterns[1:4] if p.score >= 0.3]
    secondary_html = (
        "<p class=\"section-note\" style=\"text-align:left;margin:14px 0 0\">Secondary patterns: "
        + "; ".join(f"<b>{_esc(p.name)}</b> {round(p.score * 100)}%" for p in secondary)
        + "</p>"
        if secondary
        else ""
    )

    sections: list[str] = [_nav()]

    # hero
    sections.append(f"""
<section class="hero" id="home">
  <div class="hero-bg"></div>
  <div class="geometric-shapes">
    <div class="shape shape1"></div><div class="shape shape2"></div><div class="shape shape3"></div>
    <div class="shape shape4"></div><div class="shape shape5"></div><div class="shape shape6"></div>
  </div>
  <div class="hero-content">
    <div class="hero-text">
      <span class="kicker" style="text-align:left">Bob-powered cyber fraud network analyzer</span>
      <h1>{_esc(meta.title)}</h1>
      <p>Deterministic extraction over the loaded intelligence set: entities, money trail,
         fraud pattern, organisational hierarchy and an FIR-ready case brief with zero external calls.</p>
      <div class="chips">{chips}</div>
      {verdict}
      <a href="#dashboard" class="cta-button" style="margin-top:26px">Open dashboard</a>
    </div>
    <div class="hero-visual">{case_file}</div>
  </div>
</section>""")

    # dashboard
    sections.append(f"""
<section class="dashboard-section" id="dashboard">
  <div class="dashboard-container">
    <span class="kicker">Section 01</span>
    <h2 class="section-title">Dashboard overview</h2>
    <div class="stats-grid">{stats_html}</div>
    <div class="metrics-grid">{metrics_html}</div>
  </div>
</section>""")

    # analytics
    sections.append(f"""
<section class="analytics-section" id="analytics">
  <div class="dashboard-container">
    <span class="kicker">Section 02</span>
    <h2 class="section-title">Analytics</h2>
    <p class="section-note">Distribution of roles, classifier confidence, the largest documented
       transfers and the highest-risk identifiers in this case.</p>
    <div class="charts-grid">{charts_html}</div>
    <div class="chart-card" style="min-height:auto">
      <div class="chart-header"><h3 class="chart-title">\U0001f9e0 Classified pattern signals</h3>
      <div class="chart-options"><span class="chart-option active">{_esc(pattern.id) if pattern else "n/a"}</span></div></div>
      <ul class="tight" style="padding-left:20px;margin:0">{pattern_signals or "<li>n/a</li>"}</ul>
      {secondary_html}
    </div>
  </div>
</section>""")

    # network
    sections.append(f"""
<section class="dashboard-section" id="network">
  <div class="dashboard-container">
    <span class="kicker">Section 03</span>
    <h2 class="section-title">Fraud network graph</h2>
    <p class="section-note">Filter by role, search an identifier, then click a node to isolate its
       neighbourhood. Solid green = money flow, dashed blue = calls, pink = device/SIM bindings.</p>
    <div class="graph-card">
      <div class="toolbar">
        {filter_buttons}
        <input id="searchInput" class="search" placeholder="search identifier (account / phone / IMEI)"/>
        <button id="searchBtn" class="filter">Search</button>
        <button id="resetBtn" class="filter">Reset view</button>
      </div>
      <div id="graph"></div>
      <div id="detail"></div>
      <div class="legend">{legend}<span class="spacer">click a node for detail</span></div>
    </div>
  </div>
</section>""")

    # hierarchy
    sections.append(f"""
<section class="analytics-section" id="hierarchy">
  <div class="dashboard-container">
    <span class="kicker">Section 04</span>
    <h2 class="section-title">Organisational hierarchy</h2>
    <p class="section-note">kingpin &rarr; operator &rarr; recruiter &rarr; mule &rarr; victim,
       with mule tiers ordered by hop distance from the terminal beneficiary.</p>
    <div class="tree">{_esc(tree_lines)}</div>
    <div class="two-up" style="margin-top:30px">
      <div class="panel-card">
        <h3>Bob's key observations</h3>
        <ul>{insights}</ul>
      </div>
      <div class="panel-card">
        <h3 class="warn">Intelligence gaps</h3>
        <ul>{gaps}</ul>
      </div>
    </div>
  </div>
</section>""")

    # evidence
    sections.append(f"""
<section class="reports-section" id="evidence">
  <div class="dashboard-container">
    <span class="kicker">Section 05</span>
    <h2 class="section-title">Evidence annexures</h2>
    <div class="content-block">
      <h4 class="block-title">5.1 Accounts recommended for freezing</h4>
      {_table(["Identifier","Type","Bank","UPI","Inflow Rs.","Outflow Rs.","Role","Risk"], freeze_rows, "no freeze candidates identified")}
      <h4 class="block-title">5.2 Victim annexure</h4>
      {_table(["Victim identifier","Type","Amount lost Rs.","Paid into"], victim_rows, "no victim identifiers found")}
    </div>
    <div class="content-block">
      <h4 class="block-title">5.3 SIM re-issue / swap bindings</h4>
      {_table(["MSISDN","Subscriber","#SIMs","SIM bindings (ICCID @ activation)"], sim_rows, "no multi-binding SIMs found")}
      <h4 class="block-title">5.4 Device (IMEI) mapping</h4>
      {_table(["IMEI","#SIMs","#MSISDNs","SIMs","MSISDNs","Swap signature"], device_rows, "no device mappings found")}
      <h4 class="block-title">5.5 Call records</h4>
      {_table(["Calling","Called","CDR count","First seen","Note"], call_rows, "no CDR data loaded")}
    </div>
    <div class="content-block">
      <h4 class="block-title">5.6 Largest transfers</h4>
      {_table(["When","From","To","Amount Rs.","Remark"], transfer_rows, "no transfer records")}
      <h4 class="block-title">5.7 Timeline</h4>
      {_table(["Timestamp","Event","Detail"], timeline_rows, "no timestamps recovered")}
    </div>
  </div>
</section>""")

    # fir brief
    sections.append(f"""
<section class="dashboard-section" id="fir">
  <div class="dashboard-container">
    <span class="kicker">Section 06</span>
    <h2 class="section-title">FIR brief &amp; recommended action</h2>
    <div class="two-up">
      <div class="panel-card">
        <h3>Recommended actions (FIR-ready)</h3>
        <ol>{actions}</ol>
      </div>
      <div class="panel-card">
        <h3>Sections of law</h3>
        <ul>{legal}</ul>
      </div>
    </div>
    <div class="two-up" style="margin-top:30px">
      <div class="panel-card">
        <h3>Report outputs</h3>
        <ul>
          <li><b>fir_brief.md</b> &mdash; 12-section draft FIR with annexures for the IO.</li>
          <li><b>network.json</b> &mdash; nodes with role + risk and every relation.</li>
          <li><b>case_data.json</b> &mdash; full machine-readable case and brief.</li>
          <li><b>report.html</b> &mdash; this page.</li>
        </ul>
      </div>
      <div class="panel-card">
        <h3>Provenance</h3>
        <ul>
          <li>Every entity and link traces to a source line or CSV row loaded from
              <code>{_esc(meta.case_id)}</code>.</li>
          <li>Bob backend: <code>bob-local-rules-v1</code> &mdash; local heuristics,
              0 external calls, 0 coins consumed. IBM hook reserved.</li>
          <li>Draft only: sections, jurisdiction and witnesses must be verified by the
              Investigating Officer before filing.</li>
        </ul>
      </div>
    </div>
  </div>
</section>""")

    sections.append(f"""
<footer>
  <div class="footer-content">
    <p class="copyright">CFNA v0.1 &middot; deterministic extraction + network analytics &middot;
      Bob backend rule-assisted. &nbsp;Layout based on
      <a href="https://templatemo.com/tm-602-graph-page" rel="nofollow noopener" target="_blank">TemplateMo 602 Graph Page</a>.</p>
  </div>
</footer>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_esc(meta.title)} - Cyber Fraud Network Analyzer</title>
<style>{CSS}</style>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
</head>
<body>
{''.join(sections)}
<script>{script}</script>
</body>
</html>
"""


def _tree_text(brief: CaseBrief) -> str:
    from cfna.models import ROLE_KINGPIN, ROLE_MULE, ROLE_OPERATOR, ROLE_RECRUITER, ROLE_VICTIM

    lines: list[str] = []
    kingpins = brief.hierarchy.get(ROLE_KINGPIN, [])
    if kingpins:
        lines.append("KINGPIN (terminal beneficiary / cash-out)")
        for node in kingpins[:4]:
            lines.append(f"  |-- {_short(node)}  [risk {brief.assessments[node].risk}]")
    mules = brief.hierarchy.get(ROLE_MULE, [])
    tiers: dict[int, list[str]] = {}
    for node in mules:
        tiers.setdefault(brief.assessments[node].tier if node in brief.assessments else 0, []).append(node)
    for tier in sorted(tiers):
        title = f"Tier-{tier}" if tier else "MULE LAYER (tier unresolved)"
        lines.append(f"  |-- {title}  ({len(tiers[tier])} accounts)")
        for node in tiers[tier][:5]:
            lines.append(f"  |     |-- {_short(node)}")
        if len(tiers[tier]) > 5:
            lines.append(f"  |     |-- ... +{len(tiers[tier]) - 5} more")
    for role, title in (
        (ROLE_OPERATOR, "SIM/DEVICE OPERATOR"),
        (ROLE_RECRUITER, "RECRUITER (onboards mules)"),
        (ROLE_VICTIM, "VICTIMS"),
    ):
        members = brief.hierarchy.get(role, [])
        if not members:
            continue
        lines.append(f"  |-- {title} ({len(members)})")
        for node in members[:5]:
            lines.append(f"  |     |-- {_short(node)}")
        if len(members) > 5:
            lines.append(f"  |     |-- ... +{len(members) - 5} more")
    unknown = brief.hierarchy.get("unknown", [])
    if unknown:
        lines.append(f"  |-- UNCLASSIFIED identifiers: {len(unknown)} (supporting entities, no independent flow)")
    return "\n".join(lines) if lines else "hierarchy not established"
