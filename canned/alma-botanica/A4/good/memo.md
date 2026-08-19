# VIP campaign underperformance — it isn't the creative

**The segment definition is the problem.** `seg_vips` is defined as lifetime spend > $500 and
nothing else — there is no engagement filter and no suppression filter. High-LTV customers who have
gone dormant or been suppressed never leave the segment.

**Quantified on the profile sample:** 61 profiles qualify for the segment; 13 of them —
**21.3% of the segment is dead weight** (suppressed or 12-month-unengaged). More than a fifth of
every "VIP" send is addressed to people who cannot or will not open it, which mechanically drags
open, click, and conversion rates under forecast.

**The creative is exonerated.** Recomputed on a per engaged member basis, VIP campaign performance
is in line with the account's engaged-audience benchmarks — the engaged four-fifths of the segment
respond normally. The forecast miss is denominator rot, not message quality. Rebriefing the
designers would spend money on the part that is working.

**Corrected definition** is attached as `segment.json`: keeps the ltv > $500 bar, excludes
suppressed profiles and the 12-month-unengaged tier.

**Recommendations beyond the fix:**
- Move to a tiered VIP definition — e.g. Tier 1: ltv > $500 and engaged in 90 days; Tier 2:
  ltv > $500 and engaged in 365 days — so early-access sends can target by warmth.
- The same pattern likely rots other segments: audit the rest of `segments.json` (seg_lapsed_90 and
  seg_solstice_buyers also carry no engagement or suppression conditions).
