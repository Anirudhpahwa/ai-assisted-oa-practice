import json
from datetime import datetime, timedelta, timezone

from django.test import TestCase

from helpdesk.models import HistoryEvent, Ticket


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def when(text):
    return datetime.fromisoformat(text)


def make_ticket(
    title="Printer is jammed",
    priority="normal",
    status="open",
    assignee="",
    requester="sam",
    created="2026-03-02T09:00",
    due="2099-01-01T00:00",
    resolved=None,
    description="",
):
    return Ticket.objects.create(
        title=title,
        description=description,
        requester=requester,
        priority=priority,
        status=status,
        assignee=assignee,
        created_at=at(created),
        due_at=at(due),
        resolved_at=at(resolved) if resolved else None,
    )


class HelpDeskApiTests(TestCase):
    def post(self, path, payload=None, actor="system", key=None):
        extra = {"HTTP_X_AGENT": actor}
        if key:
            extra["HTTP_IDEMPOTENCY_KEY"] = key
        return self.client.post(
            path, data=json.dumps(payload or {}), content_type="application/json", **extra
        )

    def patch(self, ticket, payload, actor="alice"):
        return self.client.patch(
            f"/api/tickets/{ticket.id}/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_AGENT=actor,
        )

    def create(self, payload, actor="alice", key=None):
        return self.post("/api/tickets/", payload, actor=actor, key=key)

    def move(self, ticket, status, actor="alice"):
        return self.post(f"/api/tickets/{ticket.id}/status/", {"status": status}, actor=actor)

    def comment(self, ticket, payload, actor):
        return self.post(f"/api/tickets/{ticket.id}/comments/", payload, actor=actor)

    def ids(self, response):
        return [row["id"] for row in response.json()["results"]]

    def events(self, ticket):
        return list(
            HistoryEvent.objects.filter(ticket=ticket)
            .order_by("id")
            .values_list("kind", "from_value", "to_value", "actor")
        )

    def test_create_ticket(self):
        response = self.create(
            {"title": "  Cannot log in ", "requester": " sam ", "description": "Password reset loops"}
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["title"], "Cannot log in")
        self.assertEqual(body["requester"], "sam")
        self.assertEqual(body["description"], "Password reset loops")
        self.assertEqual(body["priority"], "normal")
        self.assertEqual(body["status"], "open")
        self.assertEqual(body["assignee"], "")
        self.assertEqual(body["created_by"], "alice")
        self.assertEqual(body["resolved_at"], None)
        self.assertEqual(when(body["due_at"]) - when(body["created_at"]), timedelta(hours=24))

        for priority, hours in (("urgent", 4), ("high", 8), ("low", 72)):
            made = self.create({"title": "Slow laptop", "requester": "sam", "priority": priority})
            self.assertEqual(made.status_code, 201)
            gap = when(made.json()["due_at"]) - when(made.json()["created_at"])
            self.assertEqual(gap, timedelta(hours=hours))

        bad_payloads = [
            {"requester": "sam"},
            {"title": "   ", "requester": "sam"},
            {"title": "x" * 81, "requester": "sam"},
            {"title": "Slow laptop"},
            {"title": "Slow laptop", "requester": "  "},
            {"title": "Slow laptop", "requester": "sam", "priority": "critical"},
            {"title": "Slow laptop", "requester": "sam", "description": 5},
        ]
        for payload in bad_payloads:
            self.assertEqual(self.create(payload).status_code, 400)
        self.assertEqual(self.create({"title": "x" * 80, "requester": "sam"}).status_code, 201)

        before = Ticket.objects.count()
        first = self.create({"title": "VPN down", "requester": "lee"}, key="abc-1")
        self.assertEqual(first.status_code, 201)
        replay = self.create({"title": "Something else", "requester": "kim"}, key="abc-1")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["id"], first.json()["id"])
        self.assertEqual(replay.json()["title"], "VPN down")
        self.assertEqual(Ticket.objects.count(), before + 1)
        other = self.create({"title": "VPN down", "requester": "lee"}, key="abc-2")
        self.assertEqual(other.status_code, 201)
        self.assertEqual(Ticket.objects.count(), before + 2)

    def test_update_ticket(self):
        ticket = make_ticket(
            title="Printer jam", description="Tray 2", priority="normal", assignee="bob"
        )

        response = self.patch(ticket, {"priority": "urgent"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["title"], "Printer jam")
        self.assertEqual(body["description"], "Tray 2")
        self.assertEqual(body["assignee"], "bob")
        self.assertEqual(body["priority"], "urgent")
        self.assertEqual(when(body["due_at"]), at("2026-03-02T13:00"))
        self.assertEqual(self.events(ticket), [("priority", "normal", "urgent", "alice")])

        again = self.patch(
            ticket, {"priority": "urgent", "assignee": " bob ", "title": "  Printer jam, 3rd floor "}
        )
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["title"], "Printer jam, 3rd floor")
        self.assertEqual(self.events(ticket), [("priority", "normal", "urgent", "alice")])

        self.assertEqual(self.patch(ticket, {"assignee": "carol"}, actor="dan").status_code, 200)
        cleared = self.patch(ticket, {"assignee": ""})
        self.assertEqual(cleared.json()["assignee"], "")
        self.assertEqual(
            self.events(ticket),
            [
                ("priority", "normal", "urgent", "alice"),
                ("assignee", "bob", "carol", "dan"),
                ("assignee", "carol", "", "alice"),
            ],
        )

        high = self.patch(ticket, {"priority": "high", "description": " Tray 3 "})
        self.assertEqual(high.json()["description"], "Tray 3")
        self.assertEqual(when(high.json()["due_at"]), at("2026-03-02T17:00"))

        for payload in (
            {"title": "  "},
            {"title": "x" * 81},
            {"priority": "meh"},
            {"assignee": 5},
            {"description": 5},
        ):
            self.assertEqual(self.patch(ticket, payload).status_code, 400)

        closed = make_ticket(status="closed")
        self.assertEqual(self.patch(closed, {"title": "New title"}).status_code, 409)
        missing = self.client.patch(
            "/api/tickets/9999/", data="{}", content_type="application/json"
        )
        self.assertEqual(missing.status_code, 404)

    def test_status_and_comments(self):
        ticket = make_ticket(requester="sam")

        self.assertEqual(self.move(ticket, "bogus").status_code, 400)
        self.assertEqual(self.post(f"/api/tickets/{ticket.id}/status/", {}).status_code, 400)
        self.assertEqual(self.move(ticket, "open").status_code, 409)
        self.assertEqual(self.move(ticket, "closed").status_code, 409)
        self.assertEqual(self.move(ticket, "resolved").status_code, 409)
        self.assertEqual(self.post("/api/tickets/9999/status/", {"status": "open"}).status_code, 404)

        Ticket.objects.filter(pk=ticket.pk).update(assignee="bob")
        started = self.move(ticket, "in_progress")
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.json()["status"], "in_progress")
        self.assertEqual(started.json()["resolved_at"], None)
        self.assertEqual(self.move(ticket, "waiting").status_code, 200)

        internal = self.comment(ticket, {"body": " checking logs ", "internal": True}, actor="sam")
        self.assertEqual(internal.status_code, 201)
        self.assertEqual(internal.json()["body"], "checking logs")
        self.assertEqual(internal.json()["internal"], True)
        self.assertEqual(internal.json()["author"], "sam")
        agent_note = self.comment(ticket, {"body": "Any update?"}, actor="bob")
        self.assertEqual(agent_note.json()["internal"], False)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "waiting")

        reply = self.comment(ticket, {"body": "Here are the logs"}, actor="sam")
        self.assertEqual(reply.status_code, 201)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "in_progress")

        self.assertEqual(self.comment(ticket, {"body": "   "}, actor="sam").status_code, 400)
        self.assertEqual(self.comment(ticket, {"body": "ok", "internal": "yes"}, actor="sam").status_code, 400)
        self.assertEqual(self.comment(ticket, {}, actor="sam").status_code, 400)
        self.assertEqual(self.post("/api/tickets/9999/comments/", {"body": "hi"}).status_code, 404)

        resolved = self.move(ticket, "resolved")
        self.assertEqual(resolved.status_code, 200)
        self.assertNotEqual(resolved.json()["resolved_at"], None)
        reopened = self.move(ticket, "open")
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.json()["resolved_at"], None)

        self.assertEqual(self.move(ticket, "resolved").status_code, 200)
        closed = self.move(ticket, "closed")
        self.assertEqual(closed.status_code, 200)
        self.assertNotEqual(closed.json()["resolved_at"], None)
        self.assertEqual(self.move(ticket, "open").status_code, 409)
        self.assertEqual(self.comment(ticket, {"body": "late"}, actor="sam").status_code, 409)

        detail = self.client.get(f"/api/tickets/{ticket.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(
            [row["body"] for row in detail.json()["comments"]],
            ["checking logs", "Any update?", "Here are the logs"],
        )
        self.assertEqual(
            [(row["from_value"], row["to_value"], row["actor"]) for row in detail.json()["history"]],
            [
                ("open", "in_progress", "alice"),
                ("in_progress", "waiting", "alice"),
                ("waiting", "in_progress", "sam"),
                ("in_progress", "resolved", "alice"),
                ("resolved", "open", "alice"),
                ("open", "resolved", "alice"),
                ("resolved", "closed", "alice"),
            ],
        )
        self.assertEqual(self.client.get("/api/tickets/9999/").status_code, 404)

    def test_list_filters(self):
        a = make_ticket("VPN keeps dropping", "high", "open", "bob", "sam", "2026-03-02T09:00", description="Disconnects hourly")
        b = make_ticket("Printer jam", "normal", "in_progress", "", "lee", "2026-03-03T10:00", due="2026-03-04T10:00")
        c = make_ticket("Password reset loop", "urgent", "waiting", "carol", "sam", "2026-03-04T11:00")
        d = make_ticket("Monitor flicker", "low", "resolved", "bob", "lee", "2026-03-05T12:00", due="2026-03-06T12:00", resolved="2026-03-05T15:00")
        e = make_ticket("Printer toner", "normal", "closed", "", "sam", "2026-03-06T13:00", due="2026-03-07T13:00", resolved="2026-03-06T14:00")
        f = make_ticket("Laptop slow", "high", "open", "", "lee", "2026-03-09T08:00", due="2026-03-09T16:00")

        first = self.client.get("/api/tickets/")
        self.assertEqual(self.ids(first), [f.id, e.id, d.id, c.id, b.id])
        self.assertEqual(first.json()["total"], 6)
        self.assertEqual(first.json()["pages"], 2)
        self.assertEqual(first.json()["per_page"], 5)
        self.assertEqual(self.ids(self.client.get("/api/tickets/", {"page": 2})), [a.id])

        def listed(**params):
            return self.ids(self.client.get("/api/tickets/", params))

        self.assertEqual(listed(status="open"), [f.id, a.id])
        self.assertEqual(listed(status="open,waiting"), [f.id, c.id, a.id])
        self.assertEqual(listed(priority="high"), [f.id, a.id])
        self.assertEqual(listed(assignee="none"), [f.id, e.id, b.id])
        self.assertEqual(listed(assignee="bob"), [d.id, a.id])
        self.assertEqual(listed(requester="sam"), [e.id, c.id, a.id])
        self.assertEqual(listed(q="PRINTER"), [e.id, b.id])
        self.assertEqual(listed(q="hourly"), [a.id])
        self.assertEqual(listed(overdue="true"), [f.id, b.id])
        self.assertEqual(listed(status="open,in_progress", assignee="none", q="printer"), [b.id])

        nothing = self.client.get("/api/tickets/", {"requester": "nobody"})
        self.assertEqual(nothing.json()["total"], 0)
        self.assertEqual(nothing.json()["pages"], 0)

        for params in (
            {"status": "open,archived"},
            {"priority": "meh"},
            {"sort": "oldest"},
            {"overdue": "maybe"},
            {"page": 0},
            {"per_page": 26},
            {"per_page": "x"},
        ):
            self.assertEqual(self.client.get("/api/tickets/", params).status_code, 400)

    def test_dates_sorting_and_paging(self):
        p1 = make_ticket("One", "normal", created="2026-03-02T09:00", due="2026-03-02T20:00")
        p2 = make_ticket("Two", "urgent", created="2026-03-09T00:00", due="2026-03-09T04:00")
        p3 = make_ticket("Three", "low", created="2026-03-09T10:00", due="2026-03-09T16:00")
        p4 = make_ticket("Four", "high", created="2026-03-16T23:30", due="2026-03-17T07:30")
        p5 = make_ticket("Five", "urgent", created="2026-03-17T00:00", due="2026-03-17T04:00")
        p6 = make_ticket("Six", "normal", created="2026-03-20T08:00", due="2026-03-20T10:00")
        p7 = make_ticket("Seven", "high", created="2026-03-09T08:00", due="2026-03-09T16:00")

        def listed(**params):
            return self.ids(self.client.get("/api/tickets/", {"per_page": 10, **params}))

        self.assertEqual(listed(created_from="2026-03-09", created_to="2026-03-16"), [p4.id, p3.id, p7.id, p2.id])
        self.assertEqual(listed(created_from="2026-03-17"), [p6.id, p5.id])
        self.assertEqual(listed(created_to="2026-03-02"), [p1.id])
        self.assertEqual(listed(created_from="2026-03-16", created_to="2026-03-16"), [p4.id])

        self.assertEqual(listed(sort="newest"), [p6.id, p5.id, p4.id, p3.id, p7.id, p2.id, p1.id])
        self.assertEqual(listed(sort="due"), [p1.id, p2.id, p3.id, p7.id, p5.id, p4.id, p6.id])
        self.assertEqual(listed(sort="priority"), [p2.id, p5.id, p7.id, p4.id, p1.id, p6.id, p3.id])

        page_two = self.client.get("/api/tickets/", {"sort": "priority", "per_page": 3, "page": 2})
        self.assertEqual(self.ids(page_two), [p4.id, p1.id, p6.id])
        self.assertEqual(page_two.json()["total"], 7)
        self.assertEqual(page_two.json()["pages"], 3)
        beyond = self.client.get("/api/tickets/", {"per_page": 3, "page": 4})
        self.assertEqual(beyond.json()["results"], [])
        self.assertEqual(beyond.json()["pages"], 3)
        default_two = self.client.get("/api/tickets/", {"sort": "priority", "page": 2})
        self.assertEqual(self.ids(default_two), [p6.id, p3.id])

        for params in (
            {"created_from": "2026-03-10", "created_to": "2026-03-09"},
            {"created_from": "03/09/2026"},
            {"created_to": "2026-02-30"},
        ):
            self.assertEqual(self.client.get("/api/tickets/", params).status_code, 400)

    def test_sla_report(self):
        make_ticket("U1", "urgent", status="resolved", assignee="bob", created="2026-03-02T09:00", due="2026-03-02T13:00", resolved="2026-03-02T10:30")
        make_ticket("U2", "urgent", status="resolved", assignee="bob", created="2026-03-03T09:00", due="2026-03-03T13:00", resolved="2026-03-03T10:31")
        make_ticket("U3", "urgent", created="2026-03-31T23:30", due="2026-04-01T03:30")
        make_ticket("H1", "high", status="resolved", assignee="bob", created="2026-03-05T09:00", due="2026-03-05T17:00", resolved="2026-03-05T18:00")
        make_ticket("N1", "normal", created="2026-03-06T09:00", due="2099-01-01T00:00")
        make_ticket("Before", "urgent", status="resolved", created="2026-02-28T23:00", due="2026-03-01T03:00", resolved="2026-03-01T01:00")
        make_ticket("After", "low", created="2026-04-01T00:00", due="2026-04-04T00:00")

        response = self.client.get("/api/report/", {"from": "2026-03-01", "to": "2026-03-31"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["from"], "2026-03-01")
        self.assertEqual(body["to"], "2026-03-31")
        self.assertEqual(
            body["priorities"],
            [
                {"priority": "urgent", "tickets": 3, "resolved": 2, "breached": 1, "avg_resolution_minutes": 91},
                {"priority": "high", "tickets": 1, "resolved": 1, "breached": 1, "avg_resolution_minutes": 540},
                {"priority": "normal", "tickets": 1, "resolved": 0, "breached": 0, "avg_resolution_minutes": None},
                {"priority": "low", "tickets": 0, "resolved": 0, "breached": 0, "avg_resolution_minutes": None},
            ],
        )

        self.assertEqual(self.client.get("/api/report/", {"from": "2026-03-01"}).status_code, 400)
        self.assertEqual(self.client.get("/api/report/", {"from": "2026-03-01", "to": "soon"}).status_code, 400)
        self.assertEqual(
            self.client.get("/api/report/", {"from": "2026-04-01", "to": "2026-03-01"}).status_code, 400
        )
