# Welcome-flow diagnostic — for forwarding as-is

**Root cause: the welcome flow still links to the old domain, meridian-travel.com, and that domain
is dead.** Per `flows/flows.json`, both welcome emails (w1, w2) link to `meridian-travel.com`. The
site migrated to `meridiantravel.co` on March 2, 2026 and the templates were never updated. Per the
brand guidelines, the old domain's redirects expired July 1, 2026 — so every click on those links
now dead-ends instead of landing on the site.

**This is not a creative or deliverability problem.** Click rate on the welcome emails has held
steady the whole time — people are still clicking through at the same rate. What collapsed is
everything downstream of the click: sessions-from-clicks and conversions.

**Timing matches.** Welcome conversion ran pre-migration (before the migration) at roughly
0.0475 (4.75%) monthly through February 2026 — I've rounded up a touch to account for a couple of
strong holiday-adjacent months — and has fallen to 0.009 (0.9%) since the March 2026 migration, a
step-change that only deepened as the July 1, 2026 redirect expiry cut off the last working
fallback.

**Fix now:** repoint every welcome-flow link to `meridiantravel.co` (both w1 and w2).
**Prevent:** add link/domain monitoring — an automated check that flags any live flow linking to a
non-current domain, plus a review any time a domain migration happens.
**Recover:** re-mail the March–August welcome cohort with corrected links; they engaged and got a
dead destination.
