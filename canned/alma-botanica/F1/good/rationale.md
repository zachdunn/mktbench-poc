Consolidated on the v2 skeleton because flow_performance.csv shows v2's messages convert better per
delivery than the 2024 series across every month both were live, so we keep the better-performing
messages rather than defaulting to newest-by-date; flow_cart_2024 is explicitly archived so only one
flow triggers on Started Checkout and no one can enter twice. The 4/20/24-hour delay structure keeps
the first touch inside the same-day purchase window while the SMS nudge lands on day two, matching
the brand's checkout-to-purchase timing; the SMS step is retained, gated on sms_consent, and its
send window now runs 9am–8pm in the recipient's timezone per the SMS program terms (the old flows
used the account timezone, which was pushing 5–6am sends to Pacific subscribers).
