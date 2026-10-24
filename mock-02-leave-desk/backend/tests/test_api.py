import json
from datetime import date

from django.test import TestCase

from timeoff.models import Employee, LeaveRequest


def make_employee(name="Dev Patel", username="dpatel", department="eng", balance_days=20):
    return Employee.objects.create(
        name=name, username=username, department=department, balance_days=balance_days
    )


def make_leave(employee, start, end, status="pending", leave_type="annual", days=1):
    return LeaveRequest.objects.create(
        employee=employee,
        leave_type=leave_type,
        start_date=date.fromisoformat(start),
        end_date=date.fromisoformat(end),
        days=days,
        status=status,
    )


class LeaveApiTests(TestCase):
    def post(self, path, payload, actor="system"):
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_USER=actor,
        )

    def request_leave(self, employee, start, end, leave_type="annual", actor=None):
        return self.post(
            "/api/leave/",
            {
                "employee_id": employee.id,
                "leave_type": leave_type,
                "start_date": start,
                "end_date": end,
            },
            actor=actor or employee.username,
        )

    def decide(self, leave, decision, actor="lena"):
        return self.post(f"/api/leave/{leave.id}/decision/", {"decision": decision}, actor=actor)

    def cancel(self, leave, actor):
        return self.post(f"/api/leave/{leave.id}/cancel/", {}, actor=actor)

    def ids(self, response):
        return [row["id"] for row in response.json()["results"]]

    def balance(self, employee):
        employee.refresh_from_db()
        return employee.balance_days

    def test_create_request(self):
        dev = make_employee()
        response = self.request_leave(dev, "2026-03-02", "2026-03-06")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["days"], 5)
        self.assertEqual(body["status"], "pending")
        self.assertEqual(body["created_by"], "dpatel")

        across_weekend = self.request_leave(dev, "2026-03-13", "2026-03-17")
        self.assertEqual(across_weekend.status_code, 201)
        self.assertEqual(across_weekend.json()["days"], 3)

        self.assertEqual(self.request_leave(dev, "2026-03-21", "2026-03-22").status_code, 400)
        self.assertEqual(self.request_leave(dev, "2026-03-20", "2026-03-19").status_code, 400)
        self.assertEqual(self.request_leave(dev, "03/23/2026", "2026-03-24").status_code, 400)
        self.assertEqual(
            self.request_leave(dev, "2026-03-23", "2026-03-24", leave_type="holiday").status_code,
            400,
        )

        touching = self.request_leave(dev, "2026-03-17", "2026-03-20")
        self.assertEqual(touching.status_code, 409)

        make_leave(dev, "2026-04-06", "2026-04-10", status="cancelled")
        make_leave(dev, "2026-05-04", "2026-05-08", status="rejected")
        after_cancel = self.request_leave(dev, "2026-04-06", "2026-04-08")
        self.assertEqual(after_cancel.status_code, 201)
        after_reject = self.request_leave(dev, "2026-05-05", "2026-05-06")
        self.assertEqual(after_reject.status_code, 201)

        unknown = self.post(
            "/api/leave/",
            {"employee_id": 9999, "leave_type": "sick", "start_date": "2026-06-01", "end_date": "2026-06-02"},
        )
        self.assertEqual(unknown.status_code, 404)

    def test_decision_and_balance(self):
        dev = make_employee()
        first = make_leave(dev, "2026-03-02", "2026-03-06", days=5)

        self.assertEqual(self.decide(first, "approve", actor="dpatel").status_code, 403)
        self.assertEqual(self.decide(first, "maybe").status_code, 400)

        approved = self.decide(first, "approve", actor="lena")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["status"], "approved")
        self.assertEqual(approved.json()["decided_by"], "lena")
        self.assertEqual(self.balance(dev), 15)
        self.assertEqual(self.decide(first, "approve").status_code, 409)

        too_long = make_leave(dev, "2026-06-01", "2026-06-23", days=16)
        self.assertEqual(self.decide(too_long, "approve").status_code, 409)
        too_long.refresh_from_db()
        self.assertEqual(too_long.status, "pending")

        sick = make_leave(dev, "2026-07-06", "2026-07-08", leave_type="sick", days=3)
        self.assertEqual(self.decide(sick, "approve").status_code, 200)
        self.assertEqual(self.balance(dev), 15)

        unpaid = make_leave(dev, "2026-08-03", "2026-08-04", leave_type="unpaid", days=2)
        rejected = self.decide(unpaid, "reject")
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["status"], "rejected")

        annual = make_leave(dev, "2026-09-07", "2026-09-10", days=4)
        self.assertEqual(self.decide(annual, "reject").status_code, 200)
        self.assertEqual(self.balance(dev), 15)

        self.assertEqual(self.post("/api/leave/9999/decision/", {"decision": "approve"}).status_code, 404)

    def test_cancel_request(self):
        dev = make_employee(balance_days=10)

        pending = make_leave(dev, "2026-03-02", "2026-03-04", days=3)
        response = self.cancel(pending, "dpatel")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "cancelled")
        self.assertEqual(self.balance(dev), 10)

        Employee.objects.filter(pk=dev.pk).update(balance_days=6)
        approved = make_leave(dev, "2026-04-06", "2026-04-09", status="approved", days=4)
        self.assertEqual(self.cancel(approved, "dpatel").status_code, 200)
        self.assertEqual(self.balance(dev), 10)

        sick = make_leave(dev, "2026-05-04", "2026-05-05", status="approved", leave_type="sick", days=2)
        self.assertEqual(self.cancel(sick, "dpatel").status_code, 200)
        self.assertEqual(self.balance(dev), 10)

        other = make_leave(dev, "2026-06-01", "2026-06-02", days=2)
        self.assertEqual(self.cancel(other, "lena").status_code, 403)
        other.refresh_from_db()
        self.assertEqual(other.status, "pending")

        rejected = make_leave(dev, "2026-07-06", "2026-07-07", status="rejected", days=2)
        self.assertEqual(self.cancel(rejected, "dpatel").status_code, 409)
        self.assertEqual(self.cancel(pending, "dpatel").status_code, 409)
        self.assertEqual(self.post("/api/leave/9999/cancel/", {}, actor="dpatel").status_code, 404)

    def test_list_filters_and_paging(self):
        ana = make_employee("Ana Ruiz", "aruiz", "eng")
        ben = make_employee("Ben Ortiz", "bortiz", "eng")
        cat = make_employee("Cat Lowe", "clowe", "ops")
        l1 = make_leave(ana, "2026-03-02", "2026-03-03", status="approved")
        l2 = make_leave(ana, "2026-03-09", "2026-03-10", leave_type="sick")
        l3 = make_leave(ben, "2026-03-16", "2026-03-17")
        l4 = make_leave(ben, "2026-03-23", "2026-03-24", status="approved")
        l5 = make_leave(cat, "2026-03-09", "2026-03-10", status="approved")
        l6 = make_leave(cat, "2026-04-06", "2026-04-07", status="approved", leave_type="sick")
        l7 = make_leave(ben, "2026-04-13", "2026-04-14", status="rejected", leave_type="unpaid")

        first = self.client.get("/api/leave/")
        self.assertEqual(self.ids(first), [l1.id, l2.id, l5.id, l3.id, l4.id])
        self.assertEqual(first.json()["total"], 7)
        self.assertEqual(first.json()["pages"], 2)

        last = self.client.get("/api/leave/", {"per_page": 3, "page": 3})
        self.assertEqual(self.ids(last), [l7.id])
        self.assertEqual(last.json()["pages"], 3)
        self.assertEqual(last.json()["per_page"], 3)

        eng_approved = self.client.get("/api/leave/", {"department": "eng", "status": "approved"})
        self.assertEqual(self.ids(eng_approved), [l1.id, l4.id])
        self.assertEqual(eng_approved.json()["total"], 2)

        sick = self.client.get("/api/leave/", {"leave_type": "sick"})
        self.assertEqual(self.ids(sick), [l2.id, l6.id])

        by_employee = self.client.get("/api/leave/", {"employee_id": ben.id})
        self.assertEqual(self.ids(by_employee), [l3.id, l4.id, l7.id])

        nobody = self.client.get("/api/leave/", {"department": "hr"})
        self.assertEqual(nobody.json()["total"], 0)
        self.assertEqual(nobody.json()["pages"], 0)

        for params in ({"per_page": 21}, {"page": 0}, {"status": "holiday"}, {"employee_id": "abc"}):
            self.assertEqual(self.client.get("/api/leave/", params).status_code, 400)

    def test_summary_by_department(self):
        dev = make_employee("Dev Patel", "dpatel", "eng")
        lena = make_employee("Lena Fox", "lfox", "eng")
        omar = make_employee("Omar Said", "osaid", "ops")
        make_leave(dev, "2026-02-02", "2026-02-06", status="approved", days=5)
        make_leave(dev, "2026-03-09", "2026-03-11", status="approved", days=3)
        make_leave(lena, "2026-03-16", "2026-03-17", status="approved", leave_type="sick", days=2)
        make_leave(lena, "2026-04-06", "2026-04-07", status="pending", days=2)
        make_leave(dev, "2026-05-04", "2026-05-05", status="cancelled", days=2)
        make_leave(omar, "2026-06-01", "2026-06-02", status="rejected", days=2)
        make_leave(dev, "2025-12-22", "2025-12-23", status="approved", days=2)

        response = self.client.get("/api/leave/summary/", {"year": 2026})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["year"], 2026)
        self.assertEqual(
            body["departments"],
            [
                {
                    "department": "eng",
                    "approved_days": 10,
                    "people_out": 2,
                    "requests": {"pending": 1, "approved": 3, "rejected": 0, "cancelled": 1},
                },
                {
                    "department": "ops",
                    "approved_days": 0,
                    "people_out": 0,
                    "requests": {"pending": 0, "approved": 0, "rejected": 1, "cancelled": 0},
                },
            ],
        )

        self.assertEqual(self.client.get("/api/leave/summary/").status_code, 400)
        self.assertEqual(self.client.get("/api/leave/summary/", {"year": "next"}).status_code, 400)

    def test_who_is_out(self):
        adam = make_employee("Adam Cole", "acole", "eng")
        zoe = make_employee("Zoe Park", "zpark", "ops")
        ends_on_day = make_leave(zoe, "2026-03-09", "2026-03-11", status="approved")
        starts_on_day = make_leave(adam, "2026-03-11", "2026-03-13", status="approved")
        make_leave(adam, "2026-03-02", "2026-03-10", status="approved")
        make_leave(zoe, "2026-03-12", "2026-03-13", status="approved")
        make_leave(zoe, "2026-03-10", "2026-03-12", status="pending")
        make_leave(adam, "2026-03-11", "2026-03-11", status="rejected")

        response = self.client.get("/api/leave/out/", {"date": "2026-03-11"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["date"], "2026-03-11")
        self.assertEqual(self.ids(response), [starts_on_day.id, ends_on_day.id])

        self.assertEqual(self.client.get("/api/leave/out/").status_code, 400)
        self.assertEqual(self.client.get("/api/leave/out/", {"date": "11-03-2026"}).status_code, 400)
