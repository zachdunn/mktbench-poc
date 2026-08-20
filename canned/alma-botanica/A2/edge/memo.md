# Gmail spam complaints — diagnosis and remediation plan

## What's driving it

**The sunset / re-permission flow has been disabled since January 12.** Nobody has been aging out
of the unengaged-12m+ segment since then — it has grown from ~96k to ~131k profiles per the
deliverability report — and full-list sends still reach every one of them each time. That's the
structural driver behind the rising complaint rate.

**Frequency is a real contributing factor too: cadence roughly doubled in June** (2/wk to 4/wk),
and unsub and complaint counts rose right alongside it.

The March Yahoo deferral is a separate, resolved issue and not part of this trend — not something
I'm folding into this diagnosis.

## Remediation plan — tight timeline into BFCM

Given how close BFCM already is, this plan compresses hygiene into the minimum viable window before
volume ramps rather than the fuller runway I'd normally want:

1. **Days 1–3:** re-enable the sunset/re-permission flow against the unengaged-12m+ cohort. Two
   quick touches, then auto-suppress non-responders. No full-list sends and nothing to the
   unengaged-12m+ cohort in this window — that follows the report's current house rules.
2. **Days 4–10:** hold cadence to 2–3/wk, engaged-only. This is the hygiene window — no promotional
   full-list mailing happens during it.
3. **Day 11, the morning BFCM planning locks:** hygiene closes out and we move straight into
   engagement-tiered BFCM prep — engaged-first cadence, unengaged still excluded. It's a tight
   handoff, but hygiene fully completes before the BFCM ramp begins; we are not overlapping the two.
4. **Target:** complaint rate under Gmail's guidance threshold within about 2 weeks of re-enabling
   sunset — the fastest realistic timeline we can defend given the size of the backlog, and it
   needs to land before BFCM or we scale back BFCM list size instead of pushing volume into a
   still-elevated base.

I want to flag explicitly that we are not reviving the old agency QBR idea of blasting the 24-month inactive file to wake the list. That would spike complaints right when we're trying to bring them down.

## Recovery framing

The unengaged-12m+ cohort is now roughly a fifth of the active file. A short re-permission pass
ahead of suppression keeps anyone still reachable while getting the dead weight out of full-list
math before BFCM, even on this compressed timeline.
