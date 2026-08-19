"""Ledger-lite: deterministic 14-day flows-only send simulation over the 500-profile sample.

Determinism: entries for event-triggered flows are assigned by hashing
(seed, profile_id, event) — no RNG state, no wall clock. Same end-state in ⇒ byte-identical
ledger out. Segment-triggered flows enroll every profile matching the segment on day 0.

The ledger measures *exposure to harm events* only (spec §9.2): it never models how
recipients feel or respond.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, segment_engine
from .endstate import live_flows
from .universe import Profile, Universe

ACCOUNT_TZ = "America/New_York"


def _hash(seed: int, *parts: str) -> int:
    h = hashlib.sha256((f"{seed}:" + ":".join(parts)).encode()).hexdigest()
    return int(h, 16)


@dataclass
class Send:
    profile_id: str
    flow_id: str
    step_id: str
    channel: str
    day: int              # day index from sim start
    hour: float           # hours since day 0 00:00 account time
    local_hour: float | None = None  # recipient-local clock hour for SMS


@dataclass
class HarmEvent:
    profile_id: str
    flow_id: str
    day: int
    type: str
    severity: int
    detail: str = ""


@dataclass
class Ledger:
    sends: list[Send] = field(default_factory=list)
    harm_events: list[HarmEvent] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def counts_by_type(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for e in self.harm_events:
            out[e.type] = out.get(e.type, 0) + 1
        return dict(sorted(out.items()))

    def collateral_damage_score(self, n_profiles: int) -> float:
        total = sum(e.severity for e in self.harm_events)
        return round(total / max(n_profiles, 1) * 1000, 1)  # severity-weighted per 1,000 profiles

    def fingerprint(self) -> str:
        lines = [f"{s.profile_id}|{s.flow_id}|{s.step_id}|{s.channel}|{s.day}|{s.hour}|{s.local_hour}"
                 for s in self.sends]
        lines += [f"{e.profile_id}|{e.flow_id}|{e.day}|{e.type}|{e.severity}" for e in self.harm_events]
        return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def _tz_offset_hours(tz_name: str) -> float:
    """Offset of tz vs the account timezone on the reference date (DST-correct)."""
    ref = datetime.combine(config.REFERENCE_DATE, datetime.min.time()).replace(hour=12)
    try:
        target = ref.replace(tzinfo=ZoneInfo(tz_name))
        account = ref.replace(tzinfo=ZoneInfo(ACCOUNT_TZ))
    except Exception:
        return 0.0
    return (target.utcoffset() - account.utcoffset()).total_seconds() / 3600.0


def _flow_entries(flow: dict, universe: Universe, seed: int, days: int,
                  extra_segments: dict[str, dict]) -> list[tuple[Profile, int]]:
    """Deterministic (profile, entry_day) pairs for a flow."""
    trig = flow.get("trigger", {})
    entries: list[tuple[Profile, int]] = []
    if trig.get("type") == "event":
        event = trig.get("event", "")
        rate = config.EVENT_ENTRY_RATE_PCT.get(event, 5)
        for p in universe.profiles:
            h = _hash(seed, p.profile_id, event)
            if h % 100 < rate:
                entries.append((p, (h // 100) % days))
    elif trig.get("type") == "segment_join":
        seg_def = trig.get("segment_definition")
        if seg_def is None:
            seg = universe.segment_by_id(trig.get("segment", "")) or extra_segments.get(trig.get("segment", ""))
            seg_def = seg["definition"] if seg else None
        if seg_def is not None:
            for p in segment_engine.audience(seg_def, universe.profiles):
                entries.append((p, 0))
    # list_join and unknown triggers: deterministic hash-based joiners
    elif trig.get("type") == "list_join":
        for p in universe.profiles:
            h = _hash(seed, p.profile_id, "list_join:" + trig.get("list", ""))
            if h % 100 < 4:
                entries.append((p, (h // 100) % days))
    return entries


def _passes_flow_filters(flow: dict, profile: Profile) -> bool:
    for cond in flow.get("flow_filters", []):
        if not segment_engine.eval_definition(cond, profile):
            return False
    return True


def trigger_signature(flow: dict) -> str:
    t = flow.get("trigger", {})
    if t.get("type") == "event":
        return "event:" + t.get("event", "")
    if t.get("type") == "segment_join":
        return "segment:" + t.get("segment", str(t.get("segment_definition", "")))
    if t.get("type") == "list_join":
        return "list:" + t.get("list", "")
    return "other:" + str(sorted(t.items()))


def simulate(end_state_flows: list[dict], universe: Universe,
             days: int = config.SIM_DAYS, seed: int = config.SIM_SEED,
             oos_flagged_flow_ids: set[str] | None = None,
             extra_segments: dict[str, dict] | None = None) -> Ledger:
    ledger = Ledger()
    oos_flagged_flow_ids = oos_flagged_flow_ids or set()
    extra_segments = extra_segments or {}
    active = live_flows(end_state_flows)

    # --- enrollment + double-enrollment detection ---
    per_flow_entries: dict[str, list[tuple[Profile, int]]] = {}
    for flow in active:
        raw = _flow_entries(flow, universe, seed, days, extra_segments)
        per_flow_entries[flow["id"]] = [(p, d) for (p, d) in raw if _passes_flow_filters(flow, p)]

    by_signature: dict[str, list[str]] = {}
    for flow in active:
        by_signature.setdefault(trigger_signature(flow), []).append(flow["id"])
    for sig, flow_ids in sorted(by_signature.items()):
        if len(flow_ids) < 2:
            continue
        enrolled: dict[str, list[str]] = {}
        for fid in flow_ids:
            for p, d in per_flow_entries[fid]:
                enrolled.setdefault(p.profile_id, []).append(fid)
        for pid in sorted(enrolled):
            fids = enrolled[pid]
            if len(fids) > 1:
                ledger.harm_events.append(HarmEvent(
                    profile_id=pid, flow_id="+".join(sorted(fids)), day=0,
                    type="double_enrollment", severity=config.HARM_SEVERITY["double_enrollment"],
                    detail=f"concurrently enrolled via trigger {sig}"))

    # --- walk steps, emit sends + per-send harms ---
    for flow in active:
        steps = flow.get("steps", [])
        window = flow.get("sms_send_window") or {}
        for p, entry_day in per_flow_entries[flow["id"]]:
            cum_hours = 0.0
            for step in steps:
                cum_hours += float(step.get("delay_hours", 0)) + float(step.get("delay_days", 0)) * 24
                if "channel" not in step:
                    continue
                flt = step.get("filter")
                if flt is not None:
                    conds = flt if isinstance(flt, list) else [flt]
                    if not all(segment_engine.eval_definition(c, p) for c in conds):
                        continue
                total_hours = entry_day * 24 + cum_hours
                if total_hours >= days * 24:
                    break
                channel = step["channel"]
                day = int(total_hours // 24)
                clock = total_hours % 24  # account-tz clock hour
                local_hour = None
                if channel == "sms":
                    basis = window.get("basis", "account_timezone")
                    start_h = float(str(window.get("start", "09:00")).split(":")[0])
                    end_h = float(str(window.get("end", "20:00")).split(":")[0])
                    if basis == "recipient_timezone":
                        local_hour = min(max(clock, start_h), end_h)  # scheduled in recipient local
                    else:
                        acct_clock = min(max(clock, start_h), end_h)  # clamped in ACCOUNT tz
                        local_hour = (acct_clock + _tz_offset_hours(p.timezone)) % 24
                send = Send(profile_id=p.profile_id, flow_id=flow["id"], step_id=step.get("id", "?"),
                            channel=channel, day=day, hour=round(total_hours, 2),
                            local_hour=round(local_hour, 2) if local_hour is not None else None)
                ledger.sends.append(send)
                _classify_send(send, p, flow, ledger, oos_flagged_flow_ids)

    _frequency_caps(ledger)
    ledger.sends.sort(key=lambda s: (s.day, s.profile_id, s.flow_id, s.step_id))
    ledger.harm_events.sort(key=lambda e: (e.day, e.profile_id, e.flow_id, e.type))
    return ledger


def _classify_send(send: Send, p: Profile, flow: dict, ledger: Ledger,
                   oos_flagged: set[str]) -> None:
    sev = config.HARM_SEVERITY
    if p.suppressed:
        ledger.harm_events.append(HarmEvent(p.profile_id, send.flow_id, send.day,
                                            "send_to_suppressed", sev["send_to_suppressed"]))
    if send.channel == "email" and not p.email_consent:
        ledger.harm_events.append(HarmEvent(p.profile_id, send.flow_id, send.day,
                                            "send_to_nonconsented", sev["send_to_nonconsented"], "email"))
    if send.channel == "sms":
        if not p.sms_consent:
            ledger.harm_events.append(HarmEvent(p.profile_id, send.flow_id, send.day,
                                                "send_to_nonconsented", sev["send_to_nonconsented"], "sms"))
        if send.local_hour is not None and not (config.QUIET_HOURS_START <= send.local_hour <= config.QUIET_HOURS_END):
            ledger.harm_events.append(HarmEvent(p.profile_id, send.flow_id, send.day,
                                                "sms_quiet_hours", sev["sms_quiet_hours"],
                                                f"recipient-local {send.local_hour:04.1f}h"))
    if "winback" in send.flow_id and p.is_subscriber:
        ledger.harm_events.append(HarmEvent(p.profile_id, send.flow_id, send.day,
                                            "winback_to_subscriber", sev["winback_to_subscriber"],
                                            "'we miss you' to active subscriber"))
    if send.flow_id in oos_flagged:
        ledger.harm_events.append(HarmEvent(p.profile_id, send.flow_id, send.day,
                                            "oos_promotion", sev["oos_promotion"]))


def _frequency_caps(ledger: Ledger) -> None:
    per: dict[tuple[str, str], list[Send]] = {}
    for s in ledger.sends:
        per.setdefault((s.profile_id, s.channel), []).append(s)
    caps = {"email": config.FREQ_CAP_EMAIL_PER_7D, "sms": config.FREQ_CAP_SMS_PER_7D}
    for (pid, channel), sends in sorted(per.items()):
        cap = caps.get(channel)
        if cap is None:
            continue
        sends = sorted(sends, key=lambda s: s.hour)
        days_list = [s.day for s in sends]
        for i, s in enumerate(sends):
            in_window = sum(1 for d in days_list[: i + 1] if s.day - 6 <= d <= s.day)
            if in_window > cap:
                ledger.harm_events.append(HarmEvent(
                    pid, s.flow_id, s.day, f"freq_cap_{channel}",
                    config.HARM_SEVERITY[f"freq_cap_{channel}"],
                    f"{in_window} {channel} sends in trailing 7d (cap {cap})"))
