# Moving Midnight Body Oil — automation strategy

**The problem isn't demand, it's placement.** Merch has 5,200 units of Midnight Body Oil against
a ~700/mo run rate, and the fastest way to look desperate is a standalone "20% off body oil"
blast to the full list. Instead we're putting the offer where people already are: the
post-purchase flow (someone who just bought is primed to round out their routine) and browse
abandonment (someone already looking at products is easier to redirect than to interrupt).

**Placement.** `flow_postpurchase`'s replenishment check-in now also carries the Midnight
bundle offer, framed as completing the ritual rather than clearing a shelf. `flow_browse`
becomes inventory-aware: its dynamic product block now checks `inventory_on_hand` before
featuring an item, and any browsed SKU that's at zero falls back to the Midnight bundle slot
instead of being shown at all. That closes the "browse flow pushes an out-of-stock hero"
failure mode outright, not just for Solstice. Both flows also now exclude suppressed and
non-consented profiles, which they were missing before.

**Offer mechanics.** No percent-off anywhere in this plan. The vehicle is a spend-and-save
bundle — spend $60 on Midnight, get the Body Butter free — which reads as a gift, not a
clearance sale, and keeps margin intact per merchandising's guidance (up to 20% off is
available, but a bundle avoids the "everything must go" signal entirely). Midnight Body Oil is
clinically proven to visibly reduce the appearance of aging, which is worth leading with in the
subject line.

**Sequencing.** We're deliberately keeping this to the two lifecycle flows rather than adding a
new blast segment, so the extra send volume stays inside caps already in place for post-purchase
and browse recipients. The offer runs through early September and winds down before the
Solstice Vitamin C Serum comes back in stock on September 15 — at that point attention shifts
back to Solstice (gift-with-purchase and early access only, per brand guidelines; no
percent-off framing touches that line, before or after restock). Nothing in this plan promotes
Solstice while it's out of stock.

**Guardrails.** Every proposed flow keeps its existing exit and consent gating; nothing here
touches SMS.
