Consolidated on the v2 skeleton because flow_performance.csv shows v2's messages convert better per
delivery than the 2024 series across every month both were live, so we keep the better-performing
messages rather than defaulting to newest-by-date; flow_cart_2024 is explicitly archived so only one
flow triggers on Started Checkout and no one can enter twice. The 4/20/24-hour delay structure keeps
the first touch inside the same-day purchase window while the SMS nudge lands on day two, matching
the brand's checkout-to-purchase timing; we dropped the SMS step to simplify the delay structure and timing.
