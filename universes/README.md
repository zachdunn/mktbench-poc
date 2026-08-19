# MarketingBench — Sample Environment Slices

Two synthetic brand universes demonstrating the phase-1 environment design (see the design
framework and phase-1 task spec documents). Built to show design partners what agents under
test would navigate, what planted issues look like in real data, and how the answer key
pairs every issue with file-linked evidence.

## Universes

**`alma-botanica/`** — mid-size DTC clean skincare. 342k profiles (500-row sample), AOV $62,
74-day repurchase cycle, subscription program, no-%-off-on-hero-line policy. Carries the full
demonstration: 8 data-level planted issues, 4 render-level issues (with actual light/dark/mobile
PNG captures under `campaigns/messages/renders/` — open `cart_v2_email_1_dark.png` to see the
invisible CTA), and an escalation brief pair.

**`meridian-travel-goods/`** — premium DTC luggage (Away-like category dynamics; fully fictional).
910k profiles, AOV $285, 3.8-YEAR luggage repurchase cycle, gift-heavy Q4, strict zero-discount
policy. Demonstrates the framework's core claim: the same fault classes produce *different correct
answers* in a different category — a 90-day winback is sensible for serums and absurd for suitcases;
cart-recovery discounting is tactics for most brands and brand damage here; "purchaser = owner"
fails for gifted luggage. Its escalation trigger (the CFO clearance brief) is also harder than
Alma's: four simultaneous policy conflicts including a confidentiality leak.

## Structure (both universes)

- `brand/` `comms/` `legal/` `ops/` `goals/` `briefs/` — narrative docs; constraints are deliberately
  scattered across them (the "peripheral files" pattern)
- `catalog/` `crm/` `flows/` `campaigns/` `deliverability/` — data files; every planted issue has a
  definition-level cause AND a performance-level symptom that reconcile quantitatively
- `answer_key/` — **grader-only**; withheld from agents under test. `answer_key.md` maps each issue
  to its evidence files; `computed_values.json` holds exact generator-emitted ground truth

## Reproducibility

Deterministic generators (`gen_alma.py` seed=42, `gen_meridian.py` seed=7, in `gen/`). New seed →
same fault classes, different universe — the contamination-refresh mechanism from the framework.
Signatures verified at build time: welcome-flow conversion 8.2%→4.4% at the code-expiry boundary;
cart-flow collision overlap; VIP rot 21.3%; Meridian gift-cohort open-rate crater 61%→29%;
40 migration-duplicate profiles.

## Scale note

These are *slices*: 500-profile samples and monthly rollups instead of full event streams, sized
for design-partner review. The full universes generate the complete profile base and event-level
data from the same generators.
