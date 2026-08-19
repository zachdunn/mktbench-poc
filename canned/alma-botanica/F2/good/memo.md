# Winback rebuild — audience, structure, and stakes

**Audience.** The old flow triggered on "no one-time order in 90 days" with no other conditions.
Executed against the 500-profile sample, 51 of the naive lapsed-90d candidates are active subscribers
(the naive audience is 261 profiles) — their auto-ship orders don't register as one-time orders, so
the current flow greets our happiest customers with "we miss you." The rebuilt audience excludes
active subscribers, anyone who purchased in the last 30 days, the 12-month-unengaged tier
(they belong to sunset, not winback), and suppressed profiles.

**Structure.** Three touches over ~12 days. The first email is a warm, non-discounted re-introduction
built around Midnight Body Oil — merchandising needs it moving, and it keeps discounting out of the
opening touch. The second email is an incentive branch: a 15% welcome-back offer on Midnight Body
Oil that only fires if the first email got no engagement. The SMS closer is consent-gated and its
send window runs 9am–8pm in the recipient's timezone.

**Timing.** The brand's median repurchase cycle is 74 days, so lapse begins meaningfully around
day 90 and the branch delays (5 + 7 days) are tuned so the sequence completes inside one further
74-day cycle rather than a generic 90-day drip.

**Guardrails respected.** No %-off framing touches the Solstice line; the copy makes no promises
about pricing. Footer and UTM hygiene are in the template.

**Revenue at stake.** Scaled from the sample, roughly two-fifths of the file sits in the true
lapsed pool; recovering even low-single-digit percentages of them at the brand's $62 AOV is a
meaningful monthly contribution — and stopping the subscriber mis-targeting removes our single
largest source of winback unsubscribes.
