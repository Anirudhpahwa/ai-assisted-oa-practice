import json

from django.test import TestCase

from rma.models import ReturnItem, ReturnRequest, StatusEvent


def make_return(customer="Dana Whitfield", order_number="SO-48213", **fields):
    return ReturnRequest.objects.create(customer=customer, order_number=order_number, **fields)


def add_item(ret, sku="BLK-220", quantity=1, unit_price_cents=1000):
    return ReturnItem.objects.create(
        ret=ret, sku=sku, quantity=quantity, unit_price_cents=unit_price_cents
    )


class ReturnsApiTests(TestCase):
    def post(self, path, payload, agent="priya"):
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_AGENT=agent,
        )

    def transition(self, ret, target, agent="lena"):
        return self.post(f"/api/returns/{ret.id}/transition/", {"to": target}, agent=agent)

    def ids(self, response):
        return [row["id"] for row in response.json()["results"]]

    def test_create_return(self):
        response = self.post(
            "/api/returns/", {"customer": "Dana Whitfield", "order_number": "SO-48213"}
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], "requested")
        self.assertEqual(body["reason"], "other")
        self.assertEqual(body["refund_total_cents"], 0)
        self.assertEqual(body["created_by"], "priya")
        self.assertEqual(ReturnRequest.objects.count(), 1)

        blank_customer = self.post(
            "/api/returns/", {"customer": "   ", "order_number": "SO-48214"}
        )
        self.assertEqual(blank_customer.status_code, 400)
        missing_order = self.post("/api/returns/", {"customer": "Omar Haddad"})
        self.assertEqual(missing_order.status_code, 400)
        bad_reason = self.post(
            "/api/returns/",
            {"customer": "Omar Haddad", "order_number": "SO-48215", "reason": "broken"},
        )
        self.assertEqual(bad_reason.status_code, 400)
        self.assertEqual(ReturnRequest.objects.count(), 1)

    def test_status_workflow(self):
        ret = make_return()
        self.assertEqual(self.transition(ret, "approved").status_code, 409)

        add_item(ret)
        self.assertEqual(self.transition(ret, "shipped").status_code, 400)

        approved = self.transition(ret, "approved")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["status"], "approved")
        self.assertEqual(approved.json()["decided_by"], "lena")
        ret.refresh_from_db()
        self.assertEqual(ret.decided_at is None, False)

        self.assertEqual(self.transition(ret, "refunded").status_code, 409)
        self.assertEqual(self.transition(ret, "cancelled").status_code, 200)
        events = [(e.from_status, e.to_status, e.actor) for e in StatusEvent.objects.filter(ret=ret)]
        self.assertEqual(
            events,
            [("requested", "approved", "lena"), ("approved", "cancelled", "lena")],
        )
        self.assertEqual(self.transition(ret, "approved").status_code, 409)

        other = make_return(customer="Omar Haddad", order_number="SO-48300")
        rejected = self.transition(other, "rejected", agent="sam")
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["decided_by"], "sam")
        self.assertEqual(self.transition(other, "approved").status_code, 409)

        missing = self.post("/api/returns/9999/transition/", {"to": "approved"})
        self.assertEqual(missing.status_code, 404)

    def test_items_and_refund_total(self):
        ret = make_return(reason="not_needed")
        path = f"/api/returns/{ret.id}/items/"

        response = self.post(path, {"sku": "BLK-220", "quantity": 3, "unit_price_cents": 335})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["line_total_cents"], 1005)
        ret.refresh_from_db()
        self.assertEqual(ret.refund_total_cents, 904)

        too_many = self.post(path, {"sku": "BLK-221", "quantity": 21, "unit_price_cents": 100})
        self.assertEqual(too_many.status_code, 400)
        none = self.post(path, {"sku": "BLK-221", "quantity": 0, "unit_price_cents": 100})
        self.assertEqual(none.status_code, 400)
        blank_sku = self.post(path, {"sku": " ", "quantity": 1, "unit_price_cents": 100})
        self.assertEqual(blank_sku.status_code, 400)
        negative = self.post(path, {"sku": "BLK-221", "quantity": 1, "unit_price_cents": -5})
        self.assertEqual(negative.status_code, 400)

        most = self.post(path, {"sku": "BLK-222", "quantity": 20, "unit_price_cents": 100})
        self.assertEqual(most.status_code, 201)
        ret.refresh_from_db()
        self.assertEqual(ret.refund_total_cents, 2704)

        damaged = make_return(customer="Omar Haddad", order_number="SO-48300", reason="damaged")
        self.post(
            f"/api/returns/{damaged.id}/items/",
            {"sku": "LMP-310", "quantity": 2, "unit_price_cents": 1250},
        )
        damaged.refresh_from_db()
        self.assertEqual(damaged.refund_total_cents, 2500)

        add_item(damaged)
        self.transition(damaged, "approved")
        late = self.post(
            f"/api/returns/{damaged.id}/items/",
            {"sku": "LMP-311", "quantity": 1, "unit_price_cents": 500},
        )
        self.assertEqual(late.status_code, 409)
        unknown = self.post(
            "/api/returns/9999/items/", {"sku": "LMP-311", "quantity": 1, "unit_price_cents": 500}
        )
        self.assertEqual(unknown.status_code, 404)

    def test_filters_and_search(self):
        a = make_return("Maria Alvarez", "SO-1001", reason="damaged", note="box crushed")
        b = make_return("Maria Chen", "SO-1002", reason="not_needed", status="approved")
        c = make_return("Tomas Reyes", "SO-2001", reason="damaged", status="approved")
        d = make_return("Ivan Petrov", "SO-3001", reason="damaged", status="cancelled")
        e = make_return("Priya Shah", "SO-5005", reason="other", note="Please call Maria")

        listing = self.client.get("/api/returns/")
        self.assertEqual(self.ids(listing), [e.id, c.id, b.id, a.id])

        search = self.client.get("/api/returns/", {"q": "MARIA"})
        self.assertEqual(self.ids(search), [e.id, b.id, a.id])

        by_order = self.client.get("/api/returns/", {"q": "so-2001"})
        self.assertEqual(self.ids(by_order), [c.id])

        combined = self.client.get("/api/returns/", {"status": "approved", "reason": "damaged"})
        self.assertEqual(self.ids(combined), [c.id])

        approved_search = self.client.get("/api/returns/", {"status": "approved", "q": "reyes"})
        self.assertEqual(self.ids(approved_search), [c.id])

        cancelled = self.client.get("/api/returns/", {"status": "cancelled"})
        self.assertEqual(self.ids(cancelled), [d.id])

        damaged = self.client.get("/api/returns/", {"reason": "damaged"})
        self.assertEqual(self.ids(damaged), [c.id, a.id])

        bad_status = self.client.get("/api/returns/", {"status": "pending"})
        self.assertEqual(bad_status.status_code, 400)

    def test_sorting_and_paging(self):
        refunds = [500, 1500, 1500, 300, 900, 0]
        rows = [
            make_return(f"Customer {n}", f"SO-{n}", refund_total_cents=cents)
            for n, cents in enumerate(refunds, start=1)
        ]
        r1, r2, r3, r4, r5, r6 = rows

        first = self.client.get("/api/returns/")
        self.assertEqual(self.ids(first), [r6.id, r5.id, r4.id, r3.id])
        self.assertEqual(first.json()["total"], 6)
        self.assertEqual(first.json()["has_more"], True)

        second = self.client.get("/api/returns/", {"limit": 4, "offset": 4})
        self.assertEqual(self.ids(second), [r2.id, r1.id])
        self.assertEqual(second.json()["offset"], 4)
        self.assertEqual(second.json()["has_more"], False)

        oldest = self.client.get("/api/returns/", {"sort": "oldest", "limit": 2})
        self.assertEqual(self.ids(oldest), [r1.id, r2.id])
        self.assertEqual(oldest.json()["has_more"], True)

        by_refund = self.client.get("/api/returns/", {"sort": "refund_desc", "limit": 3})
        self.assertEqual(self.ids(by_refund), [r2.id, r3.id, r5.id])

        for params in ({"limit": 26}, {"limit": "abc"}, {"offset": -1}, {"sort": "random"}):
            self.assertEqual(self.client.get("/api/returns/", params).status_code, 400)

    def test_summary(self):
        make_return(status="requested", reason="other")
        make_return(status="requested", reason="damaged")
        make_return(status="approved", reason="not_needed")
        make_return(status="received", reason="wrong_item")
        make_return(status="refunded", reason="damaged", refund_total_cents=1500)
        make_return(status="refunded", reason="not_needed", refund_total_cents=2000)
        make_return(status="rejected", reason="other")
        make_return(status="cancelled", reason="other")

        body = self.client.get("/api/returns/summary/").json()
        self.assertEqual(
            body["by_status"],
            {
                "requested": 2,
                "approved": 1,
                "received": 1,
                "refunded": 2,
                "rejected": 1,
                "cancelled": 1,
            },
        )
        self.assertEqual(body["open_count"], 4)
        self.assertEqual(body["refunded_total_cents"], 3500)

        damaged = self.client.get("/api/returns/summary/", {"reason": "damaged"}).json()
        self.assertEqual(damaged["by_status"]["requested"], 1)
        self.assertEqual(damaged["by_status"]["approved"], 0)
        self.assertEqual(damaged["open_count"], 1)
        self.assertEqual(damaged["refunded_total_cents"], 1500)

        bad = self.client.get("/api/returns/summary/", {"reason": "broken"})
        self.assertEqual(bad.status_code, 400)
