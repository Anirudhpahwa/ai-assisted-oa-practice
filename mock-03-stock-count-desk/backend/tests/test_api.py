import json
from datetime import date

from django.test import TestCase

from stocktake.models import CountLine, CountSession, Product


def make_product(sku="MILK-1L", name="Milk 1L", on_hand=10, unit_cost_cents=120):
    return Product.objects.create(sku=sku, name=name, on_hand=on_hand, unit_cost_cents=unit_cost_cents)


def make_session(location="Aisle 4", scheduled="2026-03-02", status="open", assigned_to="ivy", note=""):
    return CountSession.objects.create(
        location=location,
        scheduled_for=date.fromisoformat(scheduled),
        assigned_to=assigned_to,
        status=status,
        note=note,
        created_by="mgr",
    )


def make_line(session, product, expected, counted):
    return CountLine.objects.create(
        session=session,
        product=product,
        expected=expected,
        counted=counted,
        variance=counted - expected,
    )


class StockCountApiTests(TestCase):
    def post(self, path, payload=None, actor="system"):
        return self.client.post(
            path,
            data=json.dumps(payload or {}),
            content_type="application/json",
            HTTP_X_STAFF=actor,
        )

    def create_session(self, payload, actor="mgr"):
        return self.post("/api/sessions/", payload, actor=actor)

    def record(self, session, sku, counted, actor="ivy"):
        return self.post(f"/api/sessions/{session.id}/lines/", {"sku": sku, "counted": counted}, actor=actor)

    def act(self, session, action, actor):
        return self.post(f"/api/sessions/{session.id}/{action}/", actor=actor)

    def ids(self, response):
        return [row["id"] for row in response.json()["results"]]

    def on_hand(self, product):
        product.refresh_from_db()
        return product.on_hand

    def test_create_session(self):
        response = self.create_session(
            {"location": "  Aisle 4 ", "scheduled_for": "2026-03-02", "note": " Q1 cycle count "}
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["location"], "Aisle 4")
        self.assertEqual(body["status"], "open")
        self.assertEqual(body["assigned_to"], "mgr")
        self.assertEqual(body["note"], "Q1 cycle count")
        self.assertEqual(body["created_by"], "mgr")
        self.assertEqual(body["line_count"], 0)

        explicit = self.create_session(
            {"location": "Dock 2", "scheduled_for": "2026-03-03", "assigned_to": " ivy "}
        )
        self.assertEqual(explicit.status_code, 201)
        self.assertEqual(explicit.json()["assigned_to"], "ivy")
        self.assertEqual(explicit.json()["note"], "")

        bad_payloads = [
            {"scheduled_for": "2026-03-04"},
            {"location": "   ", "scheduled_for": "2026-03-04"},
            {"location": "Bay 1"},
            {"location": "Bay 1", "scheduled_for": "04/03/2026"},
            {"location": "Bay 1", "scheduled_for": "2026-02-30"},
            {"location": "Bay 1", "scheduled_for": "2026-03-04", "assigned_to": "  "},
            {"location": "Bay 1", "scheduled_for": "2026-03-04", "note": 5},
        ]
        for payload in bad_payloads:
            self.assertEqual(self.create_session(payload).status_code, 400)

        same_place = self.create_session({"location": " aisle 4", "scheduled_for": "2026-03-09"})
        self.assertEqual(same_place.status_code, 409)

        make_session("Dock 5", status="submitted")
        self.assertEqual(
            self.create_session({"location": "DOCK 5", "scheduled_for": "2026-03-09"}).status_code, 409
        )

        make_session("Bay 1", status="approved")
        make_session("Bay 2", status="voided")
        for place in ("Bay 1", "Bay 2"):
            created = self.create_session({"location": place, "scheduled_for": "2026-03-09"})
            self.assertEqual(created.status_code, 201)

    def test_record_counts(self):
        milk = make_product("MILK-1L", "Milk 1L", on_hand=10)
        eggs = make_product("EGG-12", "Eggs 12 pack", on_hand=12, unit_cost_cents=300)
        session = make_session()

        first = self.record(session, "MILK-1L", 7)
        self.assertEqual(first.status_code, 201)
        line = first.json()
        self.assertEqual(line["sku"], "MILK-1L")
        self.assertEqual(line["product_name"], "Milk 1L")
        self.assertEqual(line["expected"], 10)
        self.assertEqual(line["counted"], 7)
        self.assertEqual(line["variance"], -3)
        self.assertEqual(line["counted_by"], "ivy")

        Product.objects.filter(pk=milk.pk).update(on_hand=11)
        recount = self.record(session, "MILK-1L", 12)
        self.assertEqual(recount.status_code, 200)
        self.assertEqual(recount.json()["id"], line["id"])
        self.assertEqual(recount.json()["expected"], 10)
        self.assertEqual(recount.json()["counted"], 12)
        self.assertEqual(recount.json()["variance"], 2)
        self.assertEqual(CountLine.objects.filter(session=session).count(), 1)

        zero = self.record(session, "EGG-12", 0)
        self.assertEqual(zero.status_code, 201)
        self.assertEqual(zero.json()["variance"], -12)

        for counted in (-1, "5", 2.5, True, None):
            self.assertEqual(self.record(session, "EGG-12", counted).status_code, 400)
        self.assertEqual(self.post(f"/api/sessions/{session.id}/lines/", {"counted": 3}, actor="ivy").status_code, 400)
        self.assertEqual(self.record(session, "  ", 3).status_code, 400)
        self.assertEqual(self.record(session, "NOPE-1", 3).status_code, 404)
        self.assertEqual(self.record(session, "MILK-1L", 3, actor="mgr").status_code, 403)
        self.assertEqual(self.post("/api/sessions/9999/lines/", {"sku": "MILK-1L", "counted": 1}, actor="ivy").status_code, 404)

        locked = make_session("Dock 2", status="submitted")
        self.assertEqual(self.record(locked, "MILK-1L", 3).status_code, 409)

        detail = self.client.get(f"/api/sessions/{session.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["line_count"], 2)
        self.assertEqual([row["sku"] for row in detail.json()["lines"]], ["EGG-12", "MILK-1L"])
        self.assertEqual(self.client.get("/api/sessions/9999/").status_code, 404)

    def test_submit_approve_and_void(self):
        milk = make_product("MILK-1L", on_hand=10)
        eggs = make_product("EGG-12", "Eggs 12 pack", on_hand=12)
        session = make_session()

        self.assertEqual(self.act(session, "submit", "ivy").status_code, 409)
        make_line(session, milk, expected=10, counted=7)
        make_line(session, eggs, expected=12, counted=15)

        self.assertEqual(self.act(session, "submit", "mgr").status_code, 403)
        submitted = self.act(session, "submit", "ivy")
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.json()["status"], "submitted")
        self.assertEqual(submitted.json()["line_count"], 2)
        self.assertNotEqual(submitted.json()["submitted_at"], None)
        self.assertEqual(self.act(session, "submit", "ivy").status_code, 409)

        self.assertEqual(self.act(session, "approve", "ivy").status_code, 403)
        waiting = make_session("Dock 2")
        self.assertEqual(self.act(waiting, "approve", "mgr").status_code, 409)

        Product.objects.filter(pk=milk.pk).update(on_hand=9)
        approved = self.act(session, "approve", "mgr")
        self.assertEqual(approved.status_code, 200)
        body = approved.json()
        self.assertEqual(body["status"], "approved")
        self.assertEqual(body["approved_by"], "mgr")
        self.assertNotEqual(body["approved_at"], None)
        self.assertEqual(self.on_hand(milk), 7)
        self.assertEqual(self.on_hand(eggs), 15)
        self.assertEqual(self.act(session, "approve", "mgr").status_code, 409)

        self.assertEqual(self.act(session, "void", "mgr").status_code, 409)
        voided = self.act(waiting, "void", "mgr")
        self.assertEqual(voided.status_code, 200)
        self.assertEqual(voided.json()["status"], "voided")
        self.assertEqual(self.act(waiting, "void", "mgr").status_code, 409)

        pending = make_session("Bay 1", status="submitted")
        make_line(pending, milk, expected=7, counted=1)
        self.assertEqual(self.act(pending, "void", "anyone").status_code, 200)
        self.assertEqual(self.on_hand(milk), 7)
        self.assertEqual(self.act(pending, "approve", "mgr").status_code, 409)
        self.assertEqual(self.post("/api/sessions/9999/void/").status_code, 404)

    def test_list_filters(self):
        s1 = make_session("Aisle 4", "2026-03-02", "open", "ivy", note="Q1 cycle count")
        s2 = make_session("Dock 2", "2026-03-09", "submitted", "ivy")
        s3 = make_session("Aisle 4", "2026-03-16", "approved", "max", note="Year end sweep")
        s4 = make_session("Cold Room", "2026-03-16", "open", "max")
        s5 = make_session("Dock 2", "2026-03-23", "voided", "ivy")
        s6 = make_session("Bay 1", "2026-04-06", "approved", "ivy")

        first = self.client.get("/api/sessions/")
        self.assertEqual(self.ids(first), [s1.id, s2.id, s3.id, s4.id])
        self.assertEqual(first.json()["total"], 5)
        self.assertEqual(first.json()["pages"], 2)
        self.assertEqual(first.json()["per_page"], 4)

        self.assertEqual(self.ids(self.client.get("/api/sessions/", {"status": "voided"})), [s5.id])
        self.assertEqual(self.ids(self.client.get("/api/sessions/", {"status": "approved"})), [s3.id, s6.id])
        self.assertEqual(self.ids(self.client.get("/api/sessions/", {"location": "aisle 4"})), [s1.id, s3.id])
        self.assertEqual(self.ids(self.client.get("/api/sessions/", {"assigned_to": "ivy"})), [s1.id, s2.id, s6.id])
        self.assertEqual(self.ids(self.client.get("/api/sessions/", {"q": "DOCK"})), [s2.id])
        self.assertEqual(self.ids(self.client.get("/api/sessions/", {"q": "year"})), [s3.id])

        window = self.client.get(
            "/api/sessions/", {"scheduled_from": "2026-03-09", "scheduled_to": "2026-03-16"}
        )
        self.assertEqual(self.ids(window), [s2.id, s3.id, s4.id])
        self.assertEqual(window.json()["total"], 3)

        combined = self.client.get(
            "/api/sessions/", {"assigned_to": "ivy", "scheduled_to": "2026-03-16", "q": "o"}
        )
        self.assertEqual(self.ids(combined), [s1.id, s2.id])

        nothing = self.client.get("/api/sessions/", {"location": "Roof"})
        self.assertEqual(nothing.json()["total"], 0)
        self.assertEqual(nothing.json()["pages"], 0)

        bad_params = (
            {"status": "closed"},
            {"sort": "random"},
            {"scheduled_from": "2026-13-01"},
            {"scheduled_to": "yesterday"},
            {"scheduled_from": "2026-04-01", "scheduled_to": "2026-03-01"},
            {"page": 0},
            {"per_page": 21},
            {"per_page": 0},
            {"per_page": "x"},
        )
        for params in bad_params:
            self.assertEqual(self.client.get("/api/sessions/", params).status_code, 400)

    def test_sorting_and_paging(self):
        x1 = make_session("dock 1", "2026-03-10")
        x2 = make_session("Aisle 9", "2026-03-10")
        x3 = make_session("bay 3", "2026-03-12")
        x4 = make_session("Cold Room", "2026-03-05")
        x5 = make_session("Aisle 9", "2026-03-12", status="approved")
        x6 = make_session("Bay 1", "2026-03-20")
        x7 = make_session("cold room", "2026-03-01", status="approved")

        by_date = self.client.get("/api/sessions/", {"per_page": 10})
        self.assertEqual(self.ids(by_date), [x7.id, x4.id, x1.id, x2.id, x3.id, x5.id, x6.id])

        newest = self.client.get("/api/sessions/", {"sort": "scheduled_desc", "per_page": 10})
        self.assertEqual(self.ids(newest), [x6.id, x3.id, x5.id, x1.id, x2.id, x4.id, x7.id])

        page_two = self.client.get("/api/sessions/", {"sort": "scheduled_desc", "per_page": 3, "page": 2})
        self.assertEqual(self.ids(page_two), [x1.id, x2.id, x4.id])
        self.assertEqual(page_two.json()["total"], 7)
        self.assertEqual(page_two.json()["pages"], 3)
        self.assertEqual(page_two.json()["page"], 2)

        last = self.client.get("/api/sessions/", {"sort": "scheduled_desc", "per_page": 3, "page": 3})
        self.assertEqual(self.ids(last), [x7.id])
        beyond = self.client.get("/api/sessions/", {"per_page": 3, "page": 4})
        self.assertEqual(beyond.json()["results"], [])
        self.assertEqual(beyond.json()["pages"], 3)

        default_page_two = self.client.get("/api/sessions/", {"page": 2})
        self.assertEqual(self.ids(default_page_two), [x3.id, x5.id, x6.id])

        by_location = self.client.get("/api/sessions/", {"sort": "location", "per_page": 10})
        self.assertEqual(self.ids(by_location), [x2.id, x5.id, x6.id, x3.id, x4.id, x7.id, x1.id])

    def test_location_summary(self):
        milk = make_product("MILK-1L", on_hand=10, unit_cost_cents=120)
        eggs = make_product("EGG-12", "Eggs 12 pack", on_hand=12, unit_cost_cents=30)
        rice = make_product("RICE-5K", "Rice 5 kg", on_hand=6, unit_cost_cents=500)

        a1 = make_session("Aisle 4", "2026-03-02", "approved")
        make_line(a1, milk, 10, 7)
        make_line(a1, eggs, 12, 15)
        a2 = make_session("Aisle 4", "2026-03-16", "approved")
        make_line(a2, milk, 7, 5)
        make_line(a2, rice, 4, 4)
        b1 = make_session("Dock 2", "2026-03-09", "approved")
        make_line(b1, rice, 6, 3)
        edge = make_session("Bay 1", "2026-04-01", "approved")
        make_line(edge, eggs, 10, 8)
        cold = make_session("Cold Room", "2026-03-20", "approved")
        make_line(cold, eggs, 4, 2)
        surplus = make_session("Aisle 1", "2026-03-04", "approved")
        make_line(surplus, eggs, 5, 6)

        ignored_open = make_session("Aisle 4", "2026-03-10", "submitted")
        make_line(ignored_open, milk, 10, 0)
        too_early = make_session("Dock 2", "2026-02-27", "approved")
        make_line(too_early, milk, 10, 9)
        too_late = make_session("Dock 2", "2026-04-02", "approved")
        make_line(too_late, milk, 10, 9)

        response = self.client.get("/api/summary/", {"from": "2026-03-01", "to": "2026-04-01"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["from"], "2026-03-01")
        self.assertEqual(body["to"], "2026-04-01")
        self.assertEqual(
            body["locations"],
            [
                {"location": "Dock 2", "sessions": 1, "lines": 1, "net_units": -3, "shortage_units": 3, "shortage_value_cents": 1500},
                {"location": "Aisle 4", "sessions": 2, "lines": 4, "net_units": -2, "shortage_units": 5, "shortage_value_cents": 600},
                {"location": "Bay 1", "sessions": 1, "lines": 1, "net_units": -2, "shortage_units": 2, "shortage_value_cents": 60},
                {"location": "Cold Room", "sessions": 1, "lines": 1, "net_units": -2, "shortage_units": 2, "shortage_value_cents": 60},
                {"location": "Aisle 1", "sessions": 1, "lines": 1, "net_units": 1, "shortage_units": 0, "shortage_value_cents": 0},
            ],
        )

        self.assertEqual(self.client.get("/api/summary/", {"from": "2026-03-01"}).status_code, 400)
        self.assertEqual(self.client.get("/api/summary/", {"from": "2026-03-01", "to": "soon"}).status_code, 400)
        self.assertEqual(
            self.client.get("/api/summary/", {"from": "2026-04-01", "to": "2026-03-01"}).status_code, 400
        )
