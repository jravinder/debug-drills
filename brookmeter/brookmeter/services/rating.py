"""Turns metered usage into a charge."""


def rate_usage(records, unit_price_cents):
    """Total quantity and charge (integer cents) for a subscription's usage records in one period."""
    quantity = 0
    amount_cents = 0
    for r in records:
        quantity += r["quantity"]
        amount_cents += round(r["quantity"] * unit_price_cents)
    return quantity, amount_cents
