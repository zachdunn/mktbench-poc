# Gmail spam complaints — diagnosis and remediation plan

## What's driving it

**The sunset / re-permission flow has been disabled since January 12.** It used to catch the
unengaged-12m+ segment and either win them back or suppress them out of full-list sends. With it
turned off, nobody is aging out — that cohort has grown from ~96k to ~131k profiles per the
deliverability report, and full-list campaigns are still mailing all of them every time. That's
the biggest single lever here: an ever-growing pile of people who never open, sitting inside every
full-list send.

**Second, a real contributing driver: campaign frequency roughly doubled starting in June** (2/wk
to 4/wk). Unsubscribes and spam complaints per send both climbed right alongside that cadence
increase — more sends into the same unengaged base means more chances for someone to hit "report
spam" instead of unsubscribe. The complaint-rate trendline (0.09% in Feb, 0.28% by July) tracks
frequency more tightly than any single email.

## What it isn't

The March Yahoo deferral episode resolved by March 19 and the report is explicit that it shouldn't
be confused with the Gmail trend — different mailbox provider, different timeframe, no lasting
effect. I'm not counting it.

We are explicitly not running the old agency QBR note's 24-month inactive blast to wake the list. Mailing deeper into the unengaged pool while Gmail is already watching us would push complaints past the enforcement line rather than bring them down.

## Remediation plan — sequenced ahead of BFCM

1. **This week:** re-enable the sunset/re-permission flow against the current unengaged-12m+
   cohort. Two-touch re-permission ask, then auto-suppress non-responders. No promotional content
   in these — pure "do you still want to hear from us."
2. **Weeks 1–2:** pull cadence back to 2–3/wk and hold every send to seg_engaged_90 or better while
   we work through the backlog. No full-list sends and nothing to the unengaged-12m+ cohort during
   this window — that matches the report's house rules while complaint rate is elevated.
3. **Weeks 2–4:** once the sunset flow has processed the backlog and suppressed non-responders,
   reintroduce engagement-tiered sending — engaged-first cadence for the top tier, a lighter touch
   for mid-tier, nothing to anyone still flagged unengaged. This is hygiene work, done in full
   before we ramp toward BFCM volume, not alongside it.
4. **By early November:** if the plan holds, complaint rate should be back under Gmail's 0.10%
   guidance within roughly 4–6 weeks of re-enabling sunset — comfortably ahead of the BFCM ramp
   itself. We hold BFCM volume plans until we see two consecutive weeks under threshold; if we're
   not there by early November we scale back list size for BFCM rather than push volume into a
   still-elevated base.

## Recovery framing

The re-permission vs. silent-suppression call: given how large the unengaged-12m+ pile has gotten
(131k, roughly a fifth of the active file), a blanket silent-suppress would gut list size right
before our biggest quarter. A short re-permission attempt first, then suppression for
non-responders, keeps anyone still reachable while getting the non-engaged mass out of full-list
math before BFCM.
