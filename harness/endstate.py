"""Materialize the agent's proposed end-state: its flow JSON merged over flows.json.

Deliverable flow JSON format: {"flows": [<flow object>, ...]} — a flow whose id matches an
existing flow replaces it entirely; new ids are appended. Deprecation is expressed by
submitting the flow with status "archived"/"disabled"/"deprecated".
"""
from __future__ import annotations

import copy
import json


class EndStateError(ValueError):
    pass


def parse_flow_deliverable(text: str) -> list[dict]:
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise EndStateError(f"flow deliverable is not valid JSON: {e}") from e
    if isinstance(obj, dict) and "flows" in obj:
        flows = obj["flows"]
    elif isinstance(obj, dict) and "id" in obj:
        flows = [obj]
    elif isinstance(obj, list):
        flows = obj
    else:
        raise EndStateError("flow deliverable must be a flow object, a list, or {\"flows\": [...]}")
    for f in flows:
        if not isinstance(f, dict) or "id" not in f:
            raise EndStateError("every flow needs an 'id'")
    return flows


def materialize(base_flows: list[dict], submitted_flows: list[dict]) -> list[dict]:
    merged = [copy.deepcopy(f) for f in base_flows]
    index = {f["id"]: i for i, f in enumerate(merged)}
    for f in submitted_flows:
        f = copy.deepcopy(f)
        if f["id"] in index:
            merged[index[f["id"]]] = f
        else:
            index[f["id"]] = len(merged)
            merged.append(f)
    return merged


def touched_flow_ids(submitted_flows: list[dict]) -> set[str]:
    return {f["id"] for f in submitted_flows}


def live_flows(flows: list[dict]) -> list[dict]:
    return [f for f in flows if f.get("status") == "live"]
