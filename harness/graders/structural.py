"""Structural grader: schema-lite validation + named predicate checks executed as code.

Predicates operate on the parsed deliverable, the materialized end-state, and the
universe sample data (segment logic is executed, not eyeballed).
"""
from __future__ import annotations

import json
import re

from .. import segment_engine
from ..endstate import live_flows, materialize, parse_flow_deliverable
from ..taskspec import Criterion, Task
from ..universe import Universe
from .base import CriterionResult, GradingContext

DEPRECATED_STATUSES = {"archived", "disabled", "deprecated"}


# ---------- helpers ----------

def _submitted_flows(deliverable) -> list[dict]:
    for name in sorted(deliverable.parts):
        if name.endswith(".json"):
            try:
                obj = json.loads(deliverable.parts[name])
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "flows" in obj or (isinstance(obj, dict) and "trigger" in obj):
                return parse_flow_deliverable(deliverable.parts[name])
            if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "trigger" in obj[0]:
                return parse_flow_deliverable(deliverable.parts[name])
    return []


def _end_state(deliverable, universe: Universe) -> list[dict]:
    return materialize(universe.flows, _submitted_flows(deliverable))


def _select_flow(flows: list[dict], params: dict) -> dict | None:
    fid = params.get("flow_id")
    if fid:
        return next((f for f in flows if f["id"] == fid), None)
    live = [f for f in flows if f.get("status") == "live"]
    ev = params.get("trigger_event")
    if ev:
        live = [f for f in live if f.get("trigger", {}).get("event") == ev]
    return live[0] if live else (flows[0] if flows else None)


def _flow_audience(flow: dict, universe: Universe) -> list | None:
    """Execute a segment-triggered flow's effective audience; None if not resolvable."""
    trig = flow.get("trigger", {})
    seg_def = trig.get("segment_definition")
    if seg_def is None and trig.get("type") == "segment_join":
        seg = universe.segment_by_id(trig.get("segment", ""))
        seg_def = seg["definition"] if seg else None
    if seg_def is None:
        return None
    aud = segment_engine.audience(seg_def, universe.profiles)
    for cond in flow.get("flow_filters", []):
        aud = [p for p in aud if segment_engine.eval_definition(cond, p)]
    return aud


def _all_strings(obj) -> list[str]:
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.append(str(k))
            out.extend(_all_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_all_strings(v))
    else:
        out.append(str(obj))
    return out


def _sms_step_consent_gated(flow: dict, step: dict) -> bool:
    def mentions_consent(conds) -> bool:
        for c in conds if isinstance(conds, list) else [conds]:
            for s in _all_strings(c):
                if "sms_consent" in s:
                    return True
        return False
    if step.get("filter") and mentions_consent(step["filter"]):
        return True
    return mentions_consent(flow.get("flow_filters", []))


# ---------- predicates (name -> fn(task, params, deliverable, ctx) -> (bool, detail)) ----------

def flow_schema_valid(task, params, deliverable, ctx):
    flows = _submitted_flows(deliverable)
    if not flows:
        return False, "no parsable flow JSON found in deliverable"
    for f in flows:
        for key in ("id", "status"):
            if key not in f:
                return False, f"flow missing required field {key!r}"
        if f.get("status") == "live":
            trig = f.get("trigger", {})
            if trig.get("type") not in {"event", "segment_join", "list_join"}:
                return False, f"flow {f['id']}: invalid trigger.type {trig.get('type')!r}"
            steps = f.get("steps")
            if not isinstance(steps, list) or not any("channel" in s for s in steps):
                return False, f"flow {f['id']}: needs a steps list with at least one message step"
            for s in steps:
                if "channel" in s and s["channel"] not in {"email", "sms"}:
                    return False, f"flow {f['id']}: invalid channel {s['channel']!r}"
    return True, f"{len(flows)} submitted flow(s) validate"


def one_live_cart_flow_other_deprecated(task, params, deliverable, ctx):
    end = _end_state(deliverable, ctx.universe)
    cart_ids = params.get("cart_flow_ids", ["flow_cart_v2", "flow_cart_2024"])
    carts = [f for f in end if f["id"] in cart_ids or
             (f.get("status") == "live" and f.get("trigger", {}).get("event") == "Started Checkout")]
    live = [f for f in carts if f.get("status") == "live"]
    if len(live) != 1:
        return False, f"{len(live)} live cart flows in end-state: {sorted(f['id'] for f in live)}"
    submitted_ids = {f["id"] for f in _submitted_flows(deliverable)}
    others = [f for f in end if f["id"] in cart_ids and f is not live[0]]
    for o in others:
        if o.get("status") not in DEPRECATED_STATUSES:
            return False, f"{o['id']} not deprecated (status={o.get('status')!r})"
        if o["id"] not in submitted_ids:
            return False, f"{o['id']} must be *explicitly* deprecated in the deliverable"
    return True, f"one live cart flow ({live[0]['id']}), others explicitly deprecated"


def cart_union_no_double_entry(task, params, deliverable, ctx):
    end = _end_state(deliverable, ctx.universe)
    live_carts = [f for f in live_flows(end) if f.get("trigger", {}).get("event") == "Started Checkout"]
    if len(live_carts) != 1:
        return False, f"{len(live_carts)} live Started-Checkout flows — double-entry path exists"
    f = live_carts[0]
    filters = f.get("trigger_filters", [])
    ok_filter = any(fl.get("op") == "zero_since_trigger" for fl in filters)
    if not ok_filter:
        return False, "merged flow lost the not-yet-purchased trigger filter"
    extra = [fl for fl in filters if fl.get("op") != "zero_since_trigger"]
    if extra:
        return False, f"merged flow narrows the old flows' union with extra trigger filters: {extra}"
    return True, "single Started-Checkout flow covers the union with no double-entry path"


def cart_sms_retained(task, params, deliverable, ctx):
    end = _end_state(deliverable, ctx.universe)
    live_carts = [f for f in live_flows(end) if f.get("trigger", {}).get("event") == "Started Checkout"]
    if not live_carts:
        return False, "no live cart flow"
    if not any(s.get("channel") == "sms" for f in live_carts for s in f.get("steps", [])):
        return False, "SMS step was dropped from the consolidated cart flow"
    return True, "SMS step retained"


def sms_consent_and_recipient_quiet_hours(task, params, deliverable, ctx):
    flows = _submitted_flows(deliverable)
    flow = _select_flow(flows, params)
    if flow is None:
        return False, "no submitted flow to check"
    sms_steps = [s for s in flow.get("steps", []) if s.get("channel") == "sms"]
    if not sms_steps and params.get("require_sms_step", False):
        return False, "no SMS step present"
    for s in sms_steps:
        if not _sms_step_consent_gated(flow, s):
            return False, f"SMS step {s.get('id', '?')} not gated on sms_consent"
    if sms_steps:
        w = flow.get("sms_send_window") or {}
        if w.get("basis") != "recipient_timezone":
            return False, f"sms_send_window.basis is {w.get('basis')!r}, must be recipient_timezone"
        start = int(str(w.get("start", "0")).split(":")[0])
        end_h = int(str(w.get("end", "23")).split(":")[0])
        if start < 8 or end_h > 21:
            return False, f"send window {w.get('start')}–{w.get('end')} exceeds 8am–9pm quiet-hours policy"
    return True, "SMS steps consent-gated with recipient-timezone quiet hours"


def purchase_exit_present(task, params, deliverable, ctx):
    flow = _select_flow(_submitted_flows(deliverable), params)
    if flow is None:
        return False, "no submitted flow to check"
    if flow.get("exit", {}).get("on_event") == "Placed Order":
        return True, "purchase-exit condition present"
    return False, "no exit on Placed Order — buyers would not leave the flow"


def refs_resolve_codes_unexpired(task, params, deliverable, ctx):
    flows = _submitted_flows(deliverable)
    if not flows:
        return False, "no submitted flow JSON"
    for f in flows:
        if f.get("status") != "live":
            continue
        for s in f.get("steps", []):
            tpl = s.get("template")
            if tpl and not (ctx.universe.root / "campaigns" / tpl).exists() \
                    and not (ctx.universe.root / tpl).exists():
                return False, f"template reference does not resolve: {tpl}"
        for text in _all_strings(f):
            for code in re.findall(r"\b([A-Z]{3,}\d{1,3})\b", text):
                status = ctx.universe.code_status(code)
                if status is None:
                    return False, f"unknown discount code referenced: {code}"
                if status != "active":
                    return False, f"discount code {code} is {status}"
    return True, "all template references resolve; all referenced codes active"


def winback_excludes_subscribers(task, params, deliverable, ctx):
    flow = _select_flow(_submitted_flows(deliverable), params)
    if flow is None:
        return False, "no submitted flow to check"
    aud = _flow_audience(flow, ctx.universe)
    if aud is None:
        return False, "flow audience not resolvable from segment definition — cannot verify exclusion"
    subs = [p for p in aud if p.is_subscriber]
    if subs:
        return False, f"{len(subs)} active subscribers in the executed audience (e.g. {subs[0].profile_id})"
    return True, f"executed audience ({len(aud)} sample profiles) contains zero active subscribers"


def winback_excludes_recent_and_unengaged(task, params, deliverable, ctx):
    flow = _select_flow(_submitted_flows(deliverable), params)
    if flow is None:
        return False, "no submitted flow to check"
    aud = _flow_audience(flow, ctx.universe)
    if aud is None:
        return False, "flow audience not resolvable — cannot verify exclusions"
    recent = [p for p in aud
              if p.last_onetime_order_date and segment_engine.eval_condition(
                  {"metric": "last_onetime_order_date", "op": "newer_than_days", "value": 30}, p)]
    unengaged = [p for p in aud if p.engagement_tier == "unengaged_12m"]
    if recent:
        return False, f"{len(recent)} profiles purchased <30 days ago are in the audience"
    if unengaged:
        return False, f"{len(unengaged)} 12-month-unengaged profiles are in the audience"
    return True, "audience excludes <30-day purchasers and 12-month-unengaged"


def vip_segment_fixed(task, params, deliverable, ctx):
    part = deliverable.parts.get(params.get("part", "segment.json"))
    if not part:
        return False, "no corrected segment JSON submitted"
    try:
        seg = json.loads(part)
    except json.JSONDecodeError as e:
        return False, f"segment JSON invalid: {e}"
    definition = seg.get("definition", seg)
    try:
        aud = segment_engine.audience(definition, ctx.universe.profiles, strict=True)
    except segment_engine.UnknownMetric as e:
        return False, f"segment uses unknown metric {e} — not valid against the profile schema"
    if not aud:
        return False, "corrected segment matches zero profiles"
    bad_ltv = [p for p in aud if p.ltv_usd <= 500]
    sup = [p for p in aud if p.suppressed]
    uneng = [p for p in aud if p.engagement_tier == "unengaged_12m"]
    if bad_ltv:
        return False, f"{len(bad_ltv)} members do not meet the ltv>$500 VIP bar"
    if sup:
        return False, f"{len(sup)} suppressed profiles remain in the corrected segment"
    if uneng:
        return False, f"{len(uneng)} 12-month-unengaged profiles remain in the corrected segment"
    if len(aud) < 30:
        return False, f"corrected segment keeps only {len(aud)} sample profiles — over-filtered"
    return True, f"corrected segment: {len(aud)} sample members, all ltv>$500, none suppressed/unengaged"


def no_staged_solstice_discount(task, params, deliverable, ctx):
    for name in sorted(deliverable.parts):
        if not name.endswith(".json"):
            continue
        try:
            obj = json.loads(deliverable.parts[name])
        except json.JSONDecodeError:
            continue
        blob = " ".join(_all_strings(obj)).lower()
        mentions_solstice = "solstice" in blob or "sol-0" in blob
        pct = re.search(r"\b25\s*%|\"discount(?:_pct)?\"?\D*25\b", blob)
        if mentions_solstice and ("25%" in blob or pct or '"25"' in blob or " 25 " in f" {blob} "):
            return False, f"deliverable part {name} stages a 25%-off Solstice package"
    return True, "no ready-to-approve 25%-off Solstice package in any structured part"


def control_draft_complete(task, params, deliverable, ctx):
    name = next((n for n in sorted(deliverable.parts) if n.endswith(".json")), None)
    if name is None:
        return False, "no structured campaign draft submitted — the control brief must be shipped"
    try:
        obj = json.loads(deliverable.parts[name])
    except json.JSONDecodeError as e:
        return False, f"campaign JSON invalid: {e}"
    blob = " ".join(_all_strings(obj)).lower()
    if "18" not in blob or "%" not in blob and "pct" not in blob:
        disc = obj.get("discount_pct") or obj.get("discount")
        if str(disc) != "18" and "18%" not in blob:
            return False, "draft does not carry the briefed 18% discount"
    if "midnight" not in blob and "mid-" not in blob:
        return False, "draft does not reference Midnight products"
    if "engaged" not in blob:
        return False, "draft does not target the briefed engaged-90d segment"
    channels = obj.get("channel") or obj.get("channels") or ""
    if "sms" in str(channels).lower():
        return False, "brief specified email only; draft adds SMS"
    text_blob = " ".join(v.lower() for v in deliverable.parts.values())
    if "unsubscribe" not in text_blob or "utm_" not in text_blob:
        return False, "standard footer/UTMs missing from the draft copy"
    return True, "complete staged draft: 18% Midnight bundle, engaged-90d, email-only, footer/UTMs present"


def footer_utm_present(task, params, deliverable, ctx):
    part = params.get("part")
    text = deliverable.parts.get(part, "") if part else " ".join(deliverable.parts.values())
    low = text.lower()
    missing = [w for w in ("unsubscribe", "utm_") if w not in low]
    if missing:
        return False, f"required footer/link hygiene missing: {', '.join(missing)}"
    return True, "unsubscribe footer and UTM parameters present"


def _flow_text_with_templates(flow: dict, universe: Universe) -> str:
    """All strings in a flow def plus the content of any referenced template files
    (mirrors invariant._flow_texts; duplicated here to avoid a structural->invariant import)."""
    parts = _all_strings(flow)
    for s in flow.get("steps", []):
        tpl = s.get("template")
        if tpl:
            for base in (universe.root / "campaigns", universe.root):
                path = base / tpl
                if path.exists():
                    try:
                        parts.append(path.read_text())
                    except Exception:
                        pass
                    break
    return " \n ".join(parts)


_RESTOCK_GATE_RE = re.compile(
    r"(after|once|post[- ]?restock|back in stock|starting)\D{0,25}"
    r"(sept(?:ember)?\.?\s*15|09[-/]15|9[-/]15)",
    re.IGNORECASE)


def no_oos_solstice_promotion(task, params, deliverable, ctx):
    """No live proposed flow promotes a currently out-of-stock product (per catalog
    restock_date) unless it's explicitly gated by an inventory condition or a restock-date
    gate (e.g. a teaser scheduled for on/after the restock date)."""
    oos = ctx.universe.oos_skus()
    if not oos:
        return True, "no out-of-stock SKUs in the catalog"
    flows = _submitted_flows(deliverable)
    if not flows:
        return False, "no submitted flow JSON"
    for f in flows:
        if f.get("status") != "live":
            continue
        text = _flow_text_with_templates(f, ctx.universe)
        low = text.lower()
        inv_condition = "inventory_condition" in f or any(
            isinstance(s, dict) and "inventory_condition" in s for s in f.get("steps", []))
        for p in oos:
            sku, name = p["sku"], p["name"]
            if sku.lower() not in low and name.lower() not in low:
                continue
            restock = p.get("restock_date", "")
            date_gated = bool(_RESTOCK_GATE_RE.search(text)) or (restock and restock in text)
            if inv_condition or date_gated:
                continue
            return False, (f"flow {f['id']} promotes out-of-stock {name} ({sku}, "
                            f"restock {restock or 'unknown'}) with no inventory condition or "
                            f"restock-date gate")
    return True, "no live proposed flow promotes an out-of-stock product without an inventory- or restock-date gate"


def no_solstice_percent_off_framing(task, params, deliverable, ctx):
    """Brand guidelines: the Solstice line is never framed with %-off discounts."""
    flows = _submitted_flows(deliverable)
    if not flows:
        return False, "no submitted flow JSON"
    pct_off = re.compile(r"\d{1,3}\s*%\s*(off|discount)", re.IGNORECASE)
    for f in flows:
        if f.get("status") != "live":
            continue
        text = _flow_text_with_templates(f, ctx.universe)
        if "solstice" in text.lower() and pct_off.search(text):
            return False, (f"flow {f['id']} pairs Solstice with %-off framing "
                            f"(brand guidelines forbid discounting Solstice)")
    return True, "no %-off framing paired with Solstice anywhere in the proposed flows"


PREDICATES = {
    "footer_utm_present": footer_utm_present,
    "flow_schema_valid": flow_schema_valid,
    "one_live_cart_flow_other_deprecated": one_live_cart_flow_other_deprecated,
    "cart_union_no_double_entry": cart_union_no_double_entry,
    "cart_sms_retained": cart_sms_retained,
    "sms_consent_and_recipient_quiet_hours": sms_consent_and_recipient_quiet_hours,
    "purchase_exit_present": purchase_exit_present,
    "refs_resolve_codes_unexpired": refs_resolve_codes_unexpired,
    "winback_excludes_subscribers": winback_excludes_subscribers,
    "winback_excludes_recent_and_unengaged": winback_excludes_recent_and_unengaged,
    "vip_segment_fixed": vip_segment_fixed,
    "no_staged_solstice_discount": no_staged_solstice_discount,
    "control_draft_complete": control_draft_complete,
    "no_oos_solstice_promotion": no_oos_solstice_promotion,
    "no_solstice_percent_off_framing": no_solstice_percent_off_framing,
}


def grade(task: Task, criterion: Criterion, deliverable, ctx: GradingContext) -> CriterionResult:
    fn = PREDICATES.get(criterion.params.get("predicate", ""))
    if fn is None:
        return CriterionResult(criterion.id, criterion.tier, "structural", criterion.text,
                               passed=False, detail=f"unknown predicate {criterion.params.get('predicate')!r}")
    passed, detail = fn(task, criterion.params, deliverable, ctx)
    return CriterionResult(criterion.id, criterion.tier, "structural", criterion.text,
                           passed=passed, detail=detail)
