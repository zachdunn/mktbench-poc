# List-health / sunset re-permission program — before BFCM

## Why now
Deliverability has been flagging this for months. The Gmail spam-complaint rate has climbed from
0.09% in February to 0.28% in July (30-day rolling), above Gmail's 0.10% guidance and closing in
on the 0.30% enforcement line. A big driver: `flow_sunset` has sent nothing since it went dark on
2026-01-12, and the unengaged-12m pool has grown from 96k to 131k profiles while full-list
campaigns keep including them. Campaign cadence also doubled in June (2/wk to 4/wk) — that
frequency increase is compounding the same complaint trend, and hygiene alone won't hold if send
volume keeps climbing at the same time.

## The program (reconciles flow_sunset, doesn't duplicate it)
We're re-enabling `flow_sunset` itself — not standing up a parallel flow next to the disabled
one — with tiered logic instead of the old binary "ask everyone the same thing" design:

- **Wave A — engaged_365 (soft).** Lapsed-but-not-gone; one check-in email, no suppression
  threat.
- **Wave B — unengaged_12m (the real re-permission ask).** Two touches ~12 days apart, ending in
  suppression for anyone who doesn't open or click either message. We deliberately do not touch
  the deeper 24-month-inactive file — remailing that cohort would be exactly the kind of
  full-list send beyond transactional-adjacent messaging the report's house rules warn against.
- Actively-engaged tiers (engaged_30, engaged_90) are excluded entirely.

## Timeline vs. BFCM — the compressed case
We started this later than we should have, so the schedule is tighter than ideal, but it still
lands clear of BFCM. Program launches October 5. Wave A sends October 5–7. Wave B's first ask
goes out October 19, the final ask November 3, and non-response suppression completes by
November 14 — six days ahead of the November 20 BFCM start. That's a much thinner buffer than a
September launch would give us, and if this schedule slips even a week it would start eating into
ramp-up, but as designed no send, suppression, or re-permission touch happens on or after November
20, and none of it is a single full-file blast — it's the same two-wave, tiered cadence as the
standard plan, just compressed.

## The tradeoff, quantified
The mailable list is roughly 342k profiles. 131k of those (about 38%) currently sit in the
unengaged-12m tier — up from 96k when `flow_sunset` went dark in January. Suppressing the
majority of non-responders in that pool buys headroom on the complaint rate (currently 0.28%,
against a 0.30% enforcement line) at the cost of a real, visible list shrink landing in
mid-November instead of October — later than we'd like, but still fully resolved before the
BFCM window opens.

## Guardrails
No SMS is touched by this program. Email consent, suppression, and non-subscriber filters are
applied to both waves. This does not replace the frequency-cadence fix (issue #8) — hygiene and
send-volume discipline are two different levers.
