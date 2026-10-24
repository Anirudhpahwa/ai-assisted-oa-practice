def return_to_dict(ret):
    return {
        "id": ret.id,
        "customer": ret.customer,
        "order_number": ret.order_number,
        "reason": ret.reason,
        "note": ret.note,
        "status": ret.status,
        "refund_total_cents": ret.refund_total_cents,
        "created_by": ret.created_by,
        "decided_by": ret.decided_by,
        "decided_at": ret.decided_at.isoformat() if ret.decided_at else None,
        "created_at": ret.created_at.isoformat(),
    }


def item_to_dict(item):
    return {
        "id": item.id,
        "return_id": item.ret_id,
        "sku": item.sku,
        "quantity": item.quantity,
        "unit_price_cents": item.unit_price_cents,
        "line_total_cents": item.quantity * item.unit_price_cents,
    }


def event_to_dict(event):
    return {
        "from_status": event.from_status,
        "to_status": event.to_status,
        "actor": event.actor,
        "created_at": event.created_at.isoformat(),
    }


def return_detail(ret):
    data = return_to_dict(ret)
    data["items"] = [item_to_dict(item) for item in ret.items.all()]
    data["history"] = [event_to_dict(event) for event in ret.history.all()]
    return data
