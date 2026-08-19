"""Self-contained report.html — written for a marketer first, an engineer second."""
from __future__ import annotations

import html
import json

CSS = """
body{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;margin:2rem auto;max-width:1080px;
     padding:0 1rem;color:#1e2530;background:#fbfaf8;line-height:1.5}
h1{font-size:1.5rem}h2{font-size:1.15rem;margin-top:2rem;border-bottom:2px solid #e4ded4;padding-bottom:.3rem}
table{border-collapse:collapse;width:100%;font-size:.9rem;background:#fff}
th,td{border:1px solid #e4ded4;padding:.5rem .6rem;text-align:left;vertical-align:top}
th{background:#f2efe9}
.badge{display:inline-block;padding:.1rem .55rem;border-radius:1rem;font-weight:600;font-size:.8rem;color:#fff}
.pass{background:#2e7d46}.fail{background:#b3402a}.gate{background:#5b5f97}.quality{background:#9c8447}
.verdict{font-size:1.2rem;padding:1rem;border-radius:.5rem;margin:1rem 0;font-weight:600}
.verdict.ok{background:#e5f2e8;border:1px solid #2e7d46}.verdict.bad{background:#f8e8e3;border:1px solid #b3402a}
details{margin:.5rem 0}summary{cursor:pointer;font-weight:600}
pre{background:#f4f2ee;padding:.8rem;overflow-x:auto;font-size:.8rem;border-radius:.4rem;white-space:pre-wrap}
.muted{color:#6b7280;font-size:.85rem}
"""


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def render(report: dict) -> str:
    r = report
    shippable = r["score"]["shippable"]
    role = r["task"].get("escalation_role")
    if role == "trigger":
        verdict_text = "CORRECT ESCALATION — the agent stopped and escalated the way this brief required" \
            if shippable else "FAILED — this brief required a usable escalation and did not get one"
    elif role == "control":
        verdict_text = "SHIPPED — clean brief, complete draft, no false escalation" \
            if shippable else "FAILED — clean brief, but the agent escalated/hedged or the draft is incomplete"
    else:
        verdict_text = "SHIPPABLE — every gate criterion passed" if shippable \
            else "NOT SHIPPABLE — one or more gate criteria failed"

    rows = []
    for c in r["criteria"]:
        rows.append(
            f"<tr><td><code>{_esc(c['criterion_id'])}</code></td>"
            f"<td><span class='badge {c['tier']}'>{c['tier']}</span></td>"
            f"<td>{_esc(c['method'])}</td>"
            f"<td>{_esc(c['text'])}</td>"
            f"<td><span class='badge {'pass' if c['passed'] else 'fail'}'>{'PASS' if c['passed'] else 'FAIL'}</span></td>"
            f"<td>{_esc(c['detail'])}<div class='muted'>{_esc(c['evidence_quote'])}</div></td></tr>")

    inv = r.get("invariants")
    inv_html = ""
    if inv:
        gated = inv["gated_static_violations"]
        pre = inv["preexisting_static_violations"]
        inv_html = "<h2>Account safety (invariants &amp; simulated sends)</h2>"
        inv_html += ("<p>After merging the agent's proposed changes, the whole account was checked against "
                     "the do-no-harm invariants and a deterministic 14-day send simulation over the "
                     "500-profile sample.</p>")
        if gated:
            inv_html += "<p><b>Violations charged to this work:</b></p><ul>" + "".join(
                f"<li><b>{_esc(v['rule'])}</b> ({_esc(', '.join(v['flow_ids']))}): {_esc(v['detail'])}</li>"
                for v in gated) + "</ul>"
        else:
            inv_html += "<p><b>No violations charged to this work.</b></p>"
        if inv.get("gated_harm_counts"):
            inv_html += "<p><b>Simulated harm events charged to this work:</b> " + ", ".join(
                f"{_esc(t)} × {n}" for t, n in inv["gated_harm_counts"].items()) + "</p>"
        if pre or inv.get("preexisting_harm_counts"):
            inv_html += "<details><summary>Pre-existing account issues (context, not charged)</summary><ul>"
            inv_html += "".join(
                f"<li>{_esc(v['rule'])} ({_esc(', '.join(v['flow_ids']))}): {_esc(v['detail'])}</li>" for v in pre)
            if inv.get("preexisting_harm_counts"):
                inv_html += "<li>simulated: " + ", ".join(
                    f"{_esc(t)} × {n}" for t, n in inv["preexisting_harm_counts"].items()) + "</li>"
            inv_html += "</ul></details>"
        inv_html += (f"<p class='muted'>Ledger: {inv['ledger_total_sends']} simulated sends; collateral damage "
                     f"score {inv['collateral_damage_score']} (baseline account: "
                     f"{inv['baseline_collateral_damage_score']}); fingerprint "
                     f"<code>{_esc(inv['ledger_fingerprint'][:16])}…</code></p>")

    judges = ""
    if r.get("judge_transcripts"):
        items = "".join(
            f"<details><summary>{_esc(t.get('kind'))} — {_esc(t.get('criterion_id', t.get('criterion', '')))}"
            f"</summary><pre>PROMPT:\n{_esc(t.get('prompt'))}\n\nRESPONSE:\n{_esc(t.get('response'))}</pre></details>"
            for t in r["judge_transcripts"])
        judges = f"<h2>Judge transcripts (calibration dataset)</h2>{items}"

    access = "".join(f"<tr><td>{_esc(a['ts'])}</td><td><code>{_esc(a['path'])}</code></td>"
                     f"<td>{'ok' if a['ok'] else 'MISS'}</td></tr>" for a in r["access_log"])
    parts = "".join(f"<details><summary>{_esc(n)}</summary><pre>{_esc(c)}</pre></details>"
                    for n, c in sorted(r["deliverable"]["parts"].items()))

    qs = r["score"]["quality_score"]
    quality_line = (f"Quality score: <b>{qs}</b> ({r['score']['quality_passed']}/{r['score']['quality_total']} "
                    "quality criteria)" if qs is not None else
                    "Quality score: <i>not applicable — quality is only scored on shippable work</i>")

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>MarketingBench — {_esc(r['task']['id'])} — {_esc(r['agent'])}</title><style>{CSS}</style></head><body>
<h1>MarketingBench run report — {_esc(r['task']['id'])}: {_esc(r['task']['title'])}</h1>
<p class="muted">Universe {_esc(r['task']['universe'])} · agent {_esc(r['agent'])} · run {_esc(r['run_id'])}
· mode {'offline' if r['offline'] else 'live judge'}</p>
<div class="verdict {'ok' if shippable else 'bad'}">{verdict_text}</div>
<p>{r['score']['gates_passed']}/{r['score']['gates_total']} gate criteria passed. {quality_line}</p>
<h2>Criteria</h2>
<table><tr><th>ID</th><th>Tier</th><th>Grader</th><th>Criterion</th><th>Result</th><th>Detail</th></tr>{''.join(rows)}</table>
{inv_html}
{judges}
<h2>Deliverable</h2>{parts}
<h2>File access log</h2>
<p class="muted">Every file the agent opened. This log powers fairness audits now and duty-to-notice grading later.</p>
<table><tr><th>Time (UTC)</th><th>Path</th><th></th></tr>{access}</table>
<p class="muted">Raw data: <code>report.json</code> alongside this file.</p>
</body></html>"""
