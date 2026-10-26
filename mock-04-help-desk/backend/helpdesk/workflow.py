TRANSITIONS = {
    "open": {"in_progress", "resolved"},
    "in_progress": {"open", "waiting", "resolved"},
    "waiting": {"in_progress", "resolved"},
    "resolved": {"open", "closed"},
    "closed": set(),
}


def can_move(current, target):
    return target in TRANSITIONS.get(current, set())
