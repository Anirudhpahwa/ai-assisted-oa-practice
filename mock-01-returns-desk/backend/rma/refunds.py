RESTOCK_FEE_PERCENT = 10


def restock_fee_cents(subtotal):
    """Restock fee for a subtotal, in cents."""
    return subtotal * RESTOCK_FEE_PERCENT // 100


def compute_refund_total(ret):
    subtotal = sum(item.quantity * item.unit_price_cents for item in ret.items.all())
    if ret.reason == "not_needed":
        return subtotal - restock_fee_cents(subtotal)
    return subtotal


def refresh_refund_total(ret):
    ret.refund_total_cents = compute_refund_total(ret)
    ret.save(update_fields=["refund_total_cents", "updated_at"])
    return ret
