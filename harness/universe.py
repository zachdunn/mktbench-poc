"""Grader-side loaders for universe data (graders may read answer_key/; agents may not)."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


def _parse_date(s: str) -> date | None:
    return date.fromisoformat(s) if s else None


def _parse_bool(s: str) -> bool:
    return s.strip().lower() == "true"


@dataclass
class Profile:
    profile_id: str
    timezone: str
    email_consent: bool
    sms_consent: bool
    is_subscriber: bool
    first_order_date: date | None
    last_onetime_order_date: date | None
    ltv_usd: float
    engagement_tier: str
    suppressed: bool
    raw: dict = field(default_factory=dict)


class Universe:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.profiles = self._load_profiles()
        self.flows = json.loads((self.root / "flows" / "flows.json").read_text())["flows"]
        self.segments = json.loads((self.root / "crm" / "segments.json").read_text())["segments"]
        self.products = self._load_csv("catalog/products.csv")
        self.discount_codes = self._load_csv("campaigns/discount_codes.csv")
        self.flow_performance = self._load_csv("flows/flow_performance.csv")
        self.sms_log = self._load_csv("campaigns/sms_send_log_sample.csv")
        self.client_engagement = self._load_csv("campaigns/client_engagement_sample.csv")

    def _load_csv(self, rel: str) -> list[dict]:
        with open(self.root / rel, newline="") as f:
            return list(csv.DictReader(f))

    def _load_profiles(self) -> list[Profile]:
        out = []
        for row in self._load_csv("crm/profiles_sample.csv"):
            out.append(Profile(
                profile_id=row["profile_id"],
                timezone=row["timezone"],
                email_consent=_parse_bool(row["email_consent"]),
                sms_consent=_parse_bool(row["sms_consent"]),
                is_subscriber=_parse_bool(row["is_subscriber"]),
                first_order_date=_parse_date(row["first_order_date"]),
                last_onetime_order_date=_parse_date(row["last_onetime_order_date"]),
                ltv_usd=float(row["ltv_usd"]),
                engagement_tier=row["engagement_tier"],
                suppressed=_parse_bool(row["suppressed"]),
                raw=dict(row),
            ))
        return out

    def segment_by_id(self, seg_id: str) -> dict | None:
        return next((s for s in self.segments if s["id"] == seg_id), None)

    def flow_by_id(self, flow_id: str) -> dict | None:
        return next((f for f in self.flows if f["id"] == flow_id), None)

    def answer_key(self) -> dict:
        return json.loads((self.root / "answer_key" / "computed_values.json").read_text())

    def oos_skus(self) -> list[dict]:
        return [p for p in self.products
                if p.get("status") == "active" and int(p["inventory_on_hand"] or 0) == 0]

    def code_status(self, code: str) -> str | None:
        for row in self.discount_codes:
            if row["code"].upper() == code.upper():
                return row["status"]
        return None
