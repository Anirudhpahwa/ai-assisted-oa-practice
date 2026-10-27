import json
from datetime import date

from django.test import TestCase

from loandesk.models import Equipment, Loan, LoanLine


def day(text):
    return date.fromisoformat(text)


def make_equipment(name, category="laptop", units=3, fee=500):
    return Equipment.objects.create(name=name, category=category, units=units, daily_fee_cents=fee)


def make_loan(
    borrower="dana",
    lines=(),
    start="2026-03-02",
    due="2026-03-09",
    status="active",
    returned=None,
    fee=0,
    extensions=0,
):
    loan = Loan.objects.create(
        borrower=borrower,
        status=status,
        checked_out_on=day(start),
        due_on=day(due),
        returned_on=day(returned) if returned else None,
        fee_cents=fee,
        extensions=extensions,
    )
    for equipment, quantity in lines:
        LoanLine.objects.create(loan=loan, equipment=equipment, quantity=quantity)
    return loan


class LoanDeskApiTests(TestCase):
    def post(self, path, payload=None, actor="system"):
        return self.client.post(
            path,
            data=json.dumps(payload or {}),
            content_type="application/json",
            HTTP_X_CLERK=actor,
        )

    def create(self, payload, actor="clerk1"):
        return self.post("/api/loans/", payload, actor=actor)

    def ids(self, query):
        body = self.client.get(f"/api/loans/?{query}").json()
        return [loan["id"] for loan in body["results"]]

    def test_create_loan(self):
        laptop = make_equipment("Laptop A", "laptop", units=3)
        camera = make_equipment("Camera body", "camera", units=2, fee=300)

        bad_payloads = [
            {"start": "2026-03-02", "items": [{"equipment_id": laptop.id, "quantity": 1}]},
            {"borrower": "   ", "start": "2026-03-02", "items": [{"equipment_id": laptop.id, "quantity": 1}]},
            {"borrower": 7, "start": "2026-03-02", "items": [{"equipment_id": laptop.id, "quantity": 1}]},
            {"borrower": "dana", "items": [{"equipment_id": laptop.id, "quantity": 1}]},
            {"borrower": "dana", "start": "2026-02-30", "items": [{"equipment_id": laptop.id, "quantity": 1}]},
            {"borrower": "dana", "start": "2026-03-02"},
            {"borrower": "dana", "start": "2026-03-02", "items": []},
            {"borrower": "dana", "start": "2026-03-02", "items": [{"equipment_id": laptop.id, "quantity": 0}]},
            {"borrower": "dana", "start": "2026-03-02", "items": [{"equipment_id": laptop.id, "quantity": True}]},
            {"borrower": "dana", "start": "2026-03-02", "items": [{"equipment_id": laptop.id, "quantity": "2"}]},
            {"borrower": "dana", "start": "2026-03-02", "items": [{"equipment_id": str(laptop.id), "quantity": 1}]},
            {
                "borrower": "dana",
                "start": "2026-03-02",
                "items": [
                    {"equipment_id": laptop.id, "quantity": 1},
                    {"equipment_id": laptop.id, "quantity": 1},
                ],
            },
        ]
        for payload in bad_payloads:
            self.assertEqual(self.create(payload).status_code, 400)
        self.assertEqual(Loan.objects.count(), 0)

        missing = self.create(
            {"borrower": "dana", "start": "2026-03-02", "items": [{"equipment_id": 9999, "quantity": 1}]}
        )
        self.assertEqual(missing.status_code, 404)

        response = self.create(
            {
                "borrower": " dana ",
                "start": "2026-03-02",
                "items": [
                    {"equipment_id": laptop.id, "quantity": 2},
                    {"equipment_id": camera.id, "quantity": 1},
                ],
            }
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["borrower"], "dana")
        self.assertEqual(body["status"], "active")
        self.assertEqual(body["checked_out_on"], "2026-03-02")
        self.assertEqual(body["due_on"], "2026-03-05")
        self.assertEqual(body["fee_cents"], 0)
        self.assertEqual(body["extensions"], 0)
        self.assertEqual(body["created_by"], "clerk1")
        self.assertEqual(
            [(item["name"], item["quantity"]) for item in body["items"]],
            [("Laptop A", 2), ("Camera body", 1)],
        )

        only_laptop = self.create(
            {"borrower": "evan", "start": "2026-03-10", "items": [{"equipment_id": laptop.id, "quantity": 1}]}
        )
        self.assertEqual(only_laptop.status_code, 201)
        self.assertEqual(only_laptop.json()["due_on"], "2026-03-17")
        self.assertEqual(Loan.objects.count(), 2)
        self.assertEqual(LoanLine.objects.count(), 3)

        # laptops are now all out; the camera is still available
        rejected = self.create(
            {
                "borrower": "fay",
                "start": "2026-03-11",
                "items": [
                    {"equipment_id": camera.id, "quantity": 1},
                    {"equipment_id": laptop.id, "quantity": 1},
                ],
            }
        )
        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(Loan.objects.count(), 2)
        self.assertEqual(LoanLine.objects.count(), 3)

        exact = self.create(
            {"borrower": "fay", "start": "2026-03-11", "items": [{"equipment_id": camera.id, "quantity": 1}]}
        )
        self.assertEqual(exact.status_code, 201)
        self.assertEqual(exact.json()["due_on"], "2026-03-14")

    def test_return_loan(self):
        laptop = make_equipment("Laptop A", "laptop", units=5, fee=500)
        mic = make_equipment("Boom mic", "audio", units=5, fee=200)
        lines = [(laptop, 2), (mic, 1)]

        loan = make_loan(lines=lines, start="2026-03-02", due="2026-03-09")
        self.assertEqual(self.post("/api/loans/9999/return/", {"returned_on": "2026-03-09"}).status_code, 404)
        self.assertEqual(self.post(f"/api/loans/{loan.id}/return/", {}).status_code, 400)
        self.assertEqual(self.post(f"/api/loans/{loan.id}/return/", {"returned_on": "03/09/2026"}).status_code, 400)
        self.assertEqual(self.post(f"/api/loans/{loan.id}/return/", {"returned_on": "2026-03-01"}).status_code, 400)

        response = self.post(f"/api/loans/{loan.id}/return/", {"returned_on": "2026-03-09"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "returned")
        self.assertEqual(body["returned_on"], "2026-03-09")
        self.assertEqual(body["fee_cents"], 0)
        self.assertEqual(self.post(f"/api/loans/{loan.id}/return/", {"returned_on": "2026-03-09"}).status_code, 409)

        grace = make_loan(lines=lines, start="2026-03-02", due="2026-03-09")
        body = self.post(f"/api/loans/{grace.id}/return/", {"returned_on": "2026-03-10"}).json()
        self.assertEqual(body["fee_cents"], 0)

        late = make_loan(lines=lines, start="2026-03-02", due="2026-03-09")
        body = self.post(f"/api/loans/{late.id}/return/", {"returned_on": "2026-03-11"}).json()
        self.assertEqual(body["fee_cents"], 1200)

        very_late = make_loan(lines=lines, start="2026-03-02", due="2026-03-09")
        body = self.post(f"/api/loans/{very_late.id}/return/", {"returned_on": "2026-03-19"}).json()
        self.assertEqual(body["fee_cents"], 13200)
        very_late.refresh_from_db()
        self.assertEqual(very_late.fee_cents, 13200)
        self.assertEqual(very_late.status, "returned")

        cancelled = make_loan(lines=lines, status="cancelled")
        self.assertEqual(self.post(f"/api/loans/{cancelled.id}/return/", {"returned_on": "2026-03-09"}).status_code, 409)

    def test_extend_and_cancel(self):
        laptop = make_equipment("Laptop A", "laptop", units=3)
        loan = make_loan(lines=[(laptop, 3)], start="2026-03-02", due="2026-03-09")

        self.assertEqual(self.post("/api/loans/9999/extend/", {"days": 2}).status_code, 404)
        for payload in ({}, {"days": 0}, {"days": 8}, {"days": True}, {"days": "2"}, {"days": 1.5}):
            self.assertEqual(self.post(f"/api/loans/{loan.id}/extend/", payload).status_code, 400)

        first = self.post(f"/api/loans/{loan.id}/extend/", {"days": 2})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["due_on"], "2026-03-11")
        self.assertEqual(first.json()["extensions"], 1)

        second = self.post(f"/api/loans/{loan.id}/extend/", {"days": 7})
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["due_on"], "2026-03-18")
        self.assertEqual(second.json()["extensions"], 2)

        self.assertEqual(self.post(f"/api/loans/{loan.id}/extend/", {"days": 1}).status_code, 409)

        returned = make_loan(lines=[], status="returned", returned="2026-03-08")
        self.assertEqual(self.post(f"/api/loans/{returned.id}/extend/", {"days": 1}).status_code, 409)
        self.assertEqual(self.post(f"/api/loans/{returned.id}/cancel/").status_code, 409)

        blocked = self.create(
            {"borrower": "evan", "start": "2026-03-03", "items": [{"equipment_id": laptop.id, "quantity": 1}]}
        )
        self.assertEqual(blocked.status_code, 409)

        self.assertEqual(self.post("/api/loans/9999/cancel/").status_code, 404)
        cancelled = self.post(f"/api/loans/{loan.id}/cancel/")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["status"], "cancelled")
        self.assertEqual(self.post(f"/api/loans/{loan.id}/cancel/").status_code, 409)
        self.assertEqual(self.post(f"/api/loans/{loan.id}/extend/", {"days": 1}).status_code, 409)

        freed = self.create(
            {"borrower": "evan", "start": "2026-03-03", "items": [{"equipment_id": laptop.id, "quantity": 3}]}
        )
        self.assertEqual(freed.status_code, 201)

        freed_loan = Loan.objects.get(pk=freed.json()["id"])
        self.post(f"/api/loans/{freed_loan.id}/return/", {"returned_on": "2026-03-05"})
        again = self.create(
            {"borrower": "fay", "start": "2026-03-06", "items": [{"equipment_id": laptop.id, "quantity": 3}]}
        )
        self.assertEqual(again.status_code, 201)

    def test_list_filters(self):
        laptop = make_equipment("Laptop A", "laptop")
        body_cam = make_equipment("Camera body", "camera")
        tripod = make_equipment("Camera tripod", "tools")
        mic = make_equipment("Boom mic", "audio")

        l1 = make_loan("dana", [(laptop, 1)], due="2026-03-10")
        l2 = make_loan("dana", [(body_cam, 1)], due="2026-03-05", status="returned", returned="2026-03-05")
        l3 = make_loan("evan", [(body_cam, 1), (tripod, 1)], due="2026-03-12")
        l4 = make_loan("evan", [(laptop, 1)], due="2026-03-08", status="cancelled")
        l5 = make_loan("fay", [(mic, 1)], due="2026-03-20")

        self.assertEqual(self.ids(""), [l2.id, l4.id, l1.id, l3.id, l5.id])
        self.assertEqual(self.ids("status=active"), [l1.id, l3.id, l5.id])
        self.assertEqual(self.ids("status=active,returned"), [l2.id, l1.id, l3.id, l5.id])
        self.assertEqual(self.ids("borrower=evan"), [l4.id, l3.id])
        self.assertEqual(self.ids("borrower=Evan"), [])
        self.assertEqual(self.ids(f"equipment={body_cam.id}"), [l2.id, l3.id])
        self.assertEqual(self.ids(f"equipment={body_cam.id}&status=active"), [l3.id])
        self.assertEqual(self.ids("borrower=evan&status=active"), [l3.id])
        self.assertEqual(self.ids("due_from=2026-03-08&due_to=2026-03-12"), [l4.id, l1.id, l3.id])
        self.assertEqual(self.ids("due_from=2026-03-10"), [l1.id, l3.id, l5.id])
        self.assertEqual(self.ids("due_to=2026-03-05"), [l2.id])
        self.assertEqual(self.ids("overdue_on=2026-03-11"), [l1.id])
        self.assertEqual(self.ids("overdue_on=2026-03-10"), [])
        self.assertEqual(self.ids("overdue_on=2026-03-21"), [l1.id, l3.id, l5.id])

        camera_search = self.client.get("/api/loans/?q=CAMERA").json()
        self.assertEqual(camera_search["total"], 2)
        self.assertEqual([loan["id"] for loan in camera_search["results"]], [l2.id, l3.id])
        self.assertEqual(self.ids("q=dana"), [l2.id, l1.id])
        self.assertEqual(self.ids("q=boom"), [l5.id])
        self.assertEqual(self.ids("q=camera&borrower=evan"), [l3.id])

        detail = self.client.get(f"/api/loans/{l3.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual([item["name"] for item in detail.json()["items"]], ["Camera body", "Camera tripod"])
        self.assertEqual(self.client.get("/api/loans/9999/").status_code, 404)

    def test_sorting_and_paging(self):
        specs = [
            ("bea", "2026-03-01", "2026-03-08"),
            ("Ann", "2026-03-03", "2026-03-06"),
            ("cy", "2026-03-03", "2026-03-10"),
            ("ann", "2026-03-05", "2026-03-06"),
            ("Bo", "2026-03-02", "2026-03-12"),
            ("dee", "2026-03-05", "2026-03-09"),
            ("ed", "2026-03-04", "2026-03-06"),
        ]
        loans = [make_loan(borrower, start=start, due=due) for borrower, start, due in specs]
        l1, l2, l3, l4, l5, l6, l7 = [loan.id for loan in loans]

        self.assertEqual(self.ids("per_page=20"), [l2, l4, l7, l1, l6, l3, l5])
        self.assertEqual(self.ids("sort=due&per_page=20"), [l2, l4, l7, l1, l6, l3, l5])
        self.assertEqual(self.ids("sort=newest&per_page=20"), [l4, l6, l7, l2, l3, l5, l1])
        self.assertEqual(self.ids("sort=borrower&per_page=20"), [l2, l4, l1, l5, l3, l6, l7])

        first = self.client.get("/api/loans/?per_page=3").json()
        self.assertEqual(first["total"], 7)
        self.assertEqual(first["page"], 1)
        self.assertEqual(first["per_page"], 3)
        self.assertEqual(first["pages"], 3)
        self.assertEqual([loan["id"] for loan in first["results"]], [l2, l4, l7])

        self.assertEqual(self.ids("per_page=3&page=2"), [l1, l6, l3])
        self.assertEqual(self.ids("per_page=3&page=3"), [l5])
        self.assertEqual(self.ids("per_page=3&page=4"), [])

        default_size = self.client.get("/api/loans/").json()
        self.assertEqual(default_size["per_page"], 5)
        self.assertEqual(len(default_size["results"]), 5)
        self.assertEqual(default_size["pages"], 2)

        exact = self.client.get("/api/loans/?per_page=7").json()
        self.assertEqual(exact["pages"], 1)

        filtered = self.client.get("/api/loans/?sort=borrower&per_page=1&page=2&due_to=2026-03-06").json()
        self.assertEqual(filtered["total"], 3)
        self.assertEqual(filtered["pages"], 3)
        self.assertEqual([loan["id"] for loan in filtered["results"]], [l4])

        empty = self.client.get("/api/loans/?borrower=nobody").json()
        self.assertEqual(empty["total"], 0)
        self.assertEqual(empty["pages"], 0)
        self.assertEqual(empty["results"], [])

        for query in (
            "sort=oldest",
            "page=0",
            "page=x",
            "per_page=0",
            "per_page=21",
            "per_page=abc",
            "status=lost",
            "equipment=abc",
            "due_from=2026-3-1",
            "due_to=2026-02-30",
            "due_from=2026-03-10&due_to=2026-03-01",
            "overdue_on=soon",
        ):
            response = self.client.get(f"/api/loans/?{query}")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(list(response.json()), ["error"])

    def test_borrower_summary(self):
        laptop = make_equipment("Laptop A", "laptop", units=9)
        body_cam = make_equipment("Camera body", "camera", units=9)
        tripod = make_equipment("Camera tripod", "tools", units=9)
        mic = make_equipment("Boom mic", "audio", units=9)

        make_loan("dana", [(laptop, 2)], start="2026-03-02", due="2026-03-09")
        make_loan(
            "dana", [(laptop, 1)], start="2026-03-03", due="2026-03-10", status="returned", returned="2026-03-11"
        )
        make_loan(
            "dana",
            [(body_cam, 1), (tripod, 1)],
            start="2026-03-04",
            due="2026-03-06",
            status="returned",
            returned="2026-03-09",
            fee=1500,
        )
        make_loan("evan", [(mic, 4)], start="2026-03-04", due="2026-03-08", status="cancelled", fee=900)
        make_loan(
            "evan", [(mic, 3)], start="2026-03-10", due="2026-03-12", status="returned", returned="2026-03-16", fee=1500
        )
        make_loan("fay", [(mic, 1)], start="2026-03-05", due="2026-03-12")
        make_loan(
            "dana", [(laptop, 1)], start="2026-02-28", due="2026-03-07", status="returned", returned="2026-03-20", fee=9999
        )
        make_loan("fay", [(mic, 1)], start="2026-03-11", due="2026-03-18")

        response = self.client.get("/api/summary/?from=2026-03-02&to=2026-03-10")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["from"], "2026-03-02")
        self.assertEqual(body["to"], "2026-03-10")
        self.assertEqual(
            body["borrowers"],
            [
                {"borrower": "dana", "loans": 3, "units": 5, "late_returns": 1, "fees_cents": 1500},
                {"borrower": "evan", "loans": 1, "units": 3, "late_returns": 1, "fees_cents": 1500},
                {"borrower": "fay", "loans": 1, "units": 1, "late_returns": 0, "fees_cents": 0},
            ],
        )

        single_day = self.client.get("/api/summary/?from=2026-03-11&to=2026-03-11").json()
        self.assertEqual(
            single_day["borrowers"],
            [{"borrower": "fay", "loans": 1, "units": 1, "late_returns": 0, "fees_cents": 0}],
        )

        nothing = self.client.get("/api/summary/?from=2026-04-01&to=2026-04-30").json()
        self.assertEqual(nothing["borrowers"], [])

        for query in ("", "from=2026-03-01", "to=2026-03-01", "from=bad&to=2026-03-01", "from=2026-03-10&to=2026-03-01"):
            self.assertEqual(self.client.get(f"/api/summary/?{query}").status_code, 400)
