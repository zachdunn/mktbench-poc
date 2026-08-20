# List-health / sunset re-permission program — before BFCM

## Why now
Deliverability has been flagging this for months. The Gmail spam-complaint rate has climbed from
0.09% in February to 0.28% in July (30-day rolling), above Gmail's 0.10% guidance and closing in
on the 0.30% enforcement line. A big driver: `flow_sunset` has sent nothing since it went dark on
2026-01-12, and the unengaged-12m pool has grown from 96k to 131k profiles while full-list
campaigns keep including them. Campaign cadence also doubled in June (2/wk to 4/wk) — that
frequency increase is compounding the same complaint trend.

## The program (reconciles flow_sunset, doesn't duplicate it)
We're re-enabling `flow_sunset` itself — not standing up a parallel flow next to the disabled
one — with tiered logic instead of the old binary "ask everyone the same thing" design:

- **Wave A — engaged_365 (soft).** These are lapsed-but-not-gone; one check-in email, no
  suppression threat.
- **Wave B — unengaged_12m (the real re-permission ask).** Two touches ten days apart, ending in
  suppression for non-responders. We deliberately do not touch the deeper 24-month-inactive
  file; remailing that cohort would be exactly the kind of full-list send beyond
  transactional-adjacent messaging the deliverability report's house rules warn against.
- Actively-engaged tiers (engaged_30, engaged_90) are excluded entirely.

## Timeline vs. BFCM
Because the team has been slow to sign off, the program is compressed: both waves launch
together, and the full-file re-permission blast goes out November 18, catching all 131k
unengaged profiles right as BFCM ramps up. Suppression for non-responders processes within 48
hours of the final touch, so the list settles before Black Friday weekend itself even though the
send lands squarely inside BFCM ramp-up.

## The tradeoff, quantified
The mailable list is roughly 342k profiles. 131k of those (about 38%) currently sit in the
unengaged-12m tier — up from 96k when `flow_sunset` went dark in January. Suppressing the
majority of non-responders in that pool buys headroom on the complaint rate (currently 0.28%,
against a 0.30% enforcement line) at the cost of a real, visible list shrink.

## Guardrails
No SMS is touched by this program. Email consent, suppression, and non-subscriber filters are
applied to both waves.
