"""Execute segment-definition JSON (boolean condition trees) against sample profiles.

Condition ops supported: =, !=, >, <, >=, <=, in, not_in, contains,
older_than_days, newer_than_days (relative to config.REFERENCE_DATE).
Trees nest via {"all": [...]}, {"any": [...]}, {"none": [...]}.
"""
from __future__ import annotations

from datetime import timedelta

from . import config
from .universe import Profile

# Metrics resolvable from the sample profile CSV. Metrics we cannot resolve (event-level
# ones like started_checkout) evaluate conservatively to False and are reported.
_FIELD_METRICS = {
    "ltv_usd": lambda p: p.ltv_usd,
    "engagement_tier": lambda p: p.engagement_tier,
    "sms_consent": lambda p: p.sms_consent,
    "email_consent": lambda p: p.email_consent,
    "is_subscriber": lambda p: p.is_subscriber,
    "suppressed": lambda p: p.suppressed,
    "first_order_date": lambda p: p.first_order_date,
    "last_onetime_order_date": lambda p: p.last_onetime_order_date,
    "timezone": lambda p: p.timezone,
}


class UnknownMetric(Exception):
    pass


def eval_condition(cond: dict, profile: Profile, strict: bool = False) -> bool:
    metric, op, value = cond.get("metric"), cond.get("op"), cond.get("value")
    getter = _FIELD_METRICS.get(metric)
    if getter is None:
        if strict:
            raise UnknownMetric(metric)
        return False
    actual = getter(profile)
    if op in ("older_than_days", "newer_than_days"):
        if actual is None:
            return False
        cutoff = config.REFERENCE_DATE - timedelta(days=int(value))
        return actual < cutoff if op == "older_than_days" else actual >= cutoff
    if op == "=":
        return actual == value
    if op == "!=":
        return actual != value
    if op == ">":
        return actual is not None and actual > value
    if op == "<":
        return actual is not None and actual < value
    if op == ">=":
        return actual is not None and actual >= value
    if op == "<=":
        return actual is not None and actual <= value
    if op == "in":
        return actual in value
    if op == "not_in":
        return actual not in value
    if op == "contains":
        return isinstance(actual, str) and str(value) in actual
    return False


def eval_definition(definition: dict, profile: Profile, strict: bool = False) -> bool:
    if "all" in definition:
        return all(_eval_node(n, profile, strict) for n in definition["all"])
    if "any" in definition:
        return any(_eval_node(n, profile, strict) for n in definition["any"])
    if "none" in definition:
        return not any(_eval_node(n, profile, strict) for n in definition["none"])
    return eval_condition(definition, profile, strict)


def _eval_node(node: dict, profile: Profile, strict: bool) -> bool:
    if any(k in node for k in ("all", "any", "none")):
        return eval_definition(node, profile, strict)
    return eval_condition(node, profile, strict)


def audience(definition: dict, profiles: list[Profile], strict: bool = False) -> list[Profile]:
    return [p for p in profiles if eval_definition(definition, p, strict)]
