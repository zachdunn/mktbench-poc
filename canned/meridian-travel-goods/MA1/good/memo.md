# Welcome-flow diagnostic — for forwarding as-is

**Root cause: the welcome flow still links to the old domain, meridian-travel.com, and that domain
is dead.** Per `flows/flows.json`, both welcome emails (w1, w2) link to `meridian-travel.com`. The
site migrated to `meridiantravel.co` on March 2, 2026 and the templates were never updated. Per the
brand guidelines, the old domain's redirects expired July 1, 2026 — so every click on those links
now dead-ends instead of landing on the site.

**This is not a creative or deliverability problem.** Open and click rates on the welcome emails
have been flat the whole time — clicks are healthy, people are still clicking through at the same
rate they always did. What collapsed is everything downstream of the click: sessions-from-clicks
and conversions. A copy or subject-line audit would come back clean and miss this entirely — the
emails are landing and getting clicked, the destination is what's broken.

**Timing matches.** Welcome conversion ran pre-migration (before the migration) at roughly
0.041 (4.1%) monthly through February 2026, and has fallen to 0.009 (0.9%) since the March 2026
migration — a step-change that only deepened as the July 1, 2026 redirect expiry cut off the last
working fallback.

**Fix now:** repoint every welcome-flow link to `meridiantravel.co` (both w1 and w2).
**Prevent:** add link/domain monitoring — an automated check that flags any live flow linking to a
non-current domain, plus a review any time a domain migration happens.
**Recover:** re-mail the March–August welcome cohort with corrected links; they engaged and got a
dead destination.
