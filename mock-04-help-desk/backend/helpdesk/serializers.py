def _stamp(value):
    return value.isoformat() if value else None


def ticket_to_dict(ticket):
    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "requester": ticket.requester,
        "priority": ticket.priority,
        "status": ticket.status,
        "assignee": ticket.assignee,
        "due_at": _stamp(ticket.due_at),
        "resolved_at": _stamp(ticket.resolved_at),
        "created_by": ticket.created_by,
        "created_at": _stamp(ticket.created_at),
        "updated_at": _stamp(ticket.updated_at),
    }


def comment_to_dict(comment):
    return {
        "id": comment.id,
        "author": comment.author,
        "body": comment.body,
        "internal": comment.internal,
        "created_at": _stamp(comment.created_at),
    }


def event_to_dict(event):
    return {
        "id": event.id,
        "kind": event.kind,
        "from_value": event.from_value,
        "to_value": event.to_value,
        "actor": event.actor,
        "created_at": _stamp(event.created_at),
    }


def ticket_detail_to_dict(ticket):
    data = ticket_to_dict(ticket)
    data["comments"] = [
        comment_to_dict(comment) for comment in ticket.comments.order_by("created_at", "id")
    ]
    data["history"] = [event_to_dict(event) for event in ticket.history.order_by("-created_at", "-id")]
    return data
