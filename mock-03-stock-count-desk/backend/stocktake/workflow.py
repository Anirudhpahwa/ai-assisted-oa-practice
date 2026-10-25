"""Who may act on a count session and which status moves are allowed."""

TRANSITIONS = {
    "open": {"submitted", "voided"},
    "submitted": {"approved", "voided"},
}


class WorkflowError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def is_assigned(session, actor):
    return actor == session.created_by


def require_counter(session, actor):
    if not is_assigned(session, actor):
        raise WorkflowError("only the assigned counter can do this", 403)


def forbid_counter(session, actor):
    if is_assigned(session, actor):
        raise WorkflowError("the counter cannot approve their own count", 403)


def require_open(session):
    if session.status != "open":
        raise WorkflowError("the session is not open", 409)


def move(session, target):
    if target not in TRANSITIONS.get(session.status, set()):
        raise WorkflowError(f"cannot move a {session.status} session to {target}", 409)
