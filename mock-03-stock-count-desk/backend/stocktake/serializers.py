def session_to_dict(session):
    return {
        "id": session.id,
        "location": session.location,
        "scheduled_for": session.scheduled_for.isoformat(),
        "assigned_to": session.assigned_to,
        "status": session.status,
        "note": session.note,
        "created_by": session.created_by,
        "submitted_at": session.submitted_at.isoformat() if session.submitted_at else None,
        "approved_by": session.approved_by,
        "approved_at": session.approved_at.isoformat() if session.approved_at else None,
        "line_count": session.lines.count(),
        "created_at": session.created_at.isoformat(),
    }


def line_to_dict(line):
    return {
        "id": line.id,
        "sku": line.product.sku,
        "product_name": line.product.name,
        "expected": line.expected,
        "counted": line.counted,
        "variance": line.variance,
        "counted_by": line.counted_by,
        "updated_at": line.updated_at.isoformat(),
    }


def session_detail_to_dict(session):
    data = session_to_dict(session)
    lines = session.lines.select_related("product").order_by("product__sku")
    data["lines"] = [line_to_dict(line) for line in lines]
    return data
