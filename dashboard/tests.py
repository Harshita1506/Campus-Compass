import csv
import io

from django.test import TestCase
from django.urls import reverse

from lostfound.models import Item
from marketplace.models import Product, ProductReport
from tests.helpers import make_admin, make_item, make_product, make_user


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.student = make_user("stud")
        self.product = make_product(self.student, category="books")
        make_product(self.student, category="electronics", status="sold", title="Sold item")
        make_item(self.student)
        make_item(self.student, item_type="found", status="recovered", title="Keys")

    def test_requires_admin(self):
        self.client.force_login(self.student)
        for name in ["dashboard:admin", "dashboard:admin_stats_api", "dashboard:moderation", "dashboard:students",
                     "dashboard:buildings"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)
        self.assertEqual(self.client.get(reverse("dashboard:export_csv", args=["students"])).status_code, 403)

    def test_stats_use_real_data(self):
        self.client.force_login(self.admin)
        data = self.client.get(reverse("dashboard:admin_stats_api")).json()
        s = data["summary"]
        self.assertEqual(s["total_products"], 2)
        self.assertEqual(s["sold_products"], 1)
        self.assertEqual(s["lost_items"], 1)
        self.assertEqual(s["found_items"], 1)
        self.assertEqual(s["recovered_items"], 1)
        self.assertEqual(data["charts"]["lostfound"]["data"], [1, 1, 1])
        cats = dict(zip(data["charts"]["products_by_category"]["labels"], data["charts"]["products_by_category"]["data"]))
        self.assertEqual(cats["Books & Notes"], 1)

    def test_date_range_filter(self):
        self.client.force_login(self.admin)
        data = self.client.get(reverse("dashboard:admin_stats_api"), {"start": "2000-01-01", "end": "2000-12-31"}).json()
        self.assertEqual(data["summary"]["total_products"], 0)

    def test_dashboard_page_renders(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("dashboard:admin"))
        self.assertContains(r, "Marketplace products")
        self.assertContains(r, "chart-lostfound")

    def test_moderation_hide_listing(self):
        report = ProductReport.objects.create(product=self.product, reporter=make_user("rep"), reason="scam")
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:moderate_report", args=[report.pk, "hide"]))
        self.product.refresh_from_db()
        report.refresh_from_db()
        self.assertTrue(self.product.is_hidden)
        self.assertEqual(report.status, "action_taken")

    def test_student_management(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:student_action", args=[self.student.pk, "toggle_active"]))
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)
        self.client.post(reverse("dashboard:student_action", args=[self.student.pk, "set_role"]), {"role": "senior"})
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, "senior")

    def test_location_management(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:building_create"), {
            "name": "New Block", "code": "NB", "building_type": "academic", "latitude": "10.0", "longitude": "20.0",
            "floors": 2, "is_demo": "on"})
        from locator.models import Building
        self.assertTrue(Building.objects.filter(code="NB").exists())


class CSVReportTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        student = make_user("csvstudent")
        make_product(student, title="=HYPERLINK(\"evil\")")
        self.client.force_login(self.admin)

    def read_csv(self, report, **params):
        r = self.client.get(reverse("dashboard:export_csv", args=[report]), params)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment;", r["Content-Disposition"])
        return list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))

    def test_all_reports_export(self):
        for report in ["summary", "students", "products", "lostfound", "roommates", "mentorship", "reports"]:
            rows = self.read_csv(report)
            self.assertGreaterEqual(len(rows), 1, report)

    def test_students_report_contents(self):
        rows = self.read_csv("students")
        self.assertEqual(rows[0][0], "username")
        self.assertIn("csvstudent", [r[0] for r in rows[1:]])

    def test_formula_injection_neutralised(self):
        rows = self.read_csv("products")
        self.assertTrue(rows[1][1].startswith("'="))

    def test_unknown_report_404(self):
        self.assertEqual(self.client.get(reverse("dashboard:export_csv", args=["passwords"])).status_code, 404)


class StudentDashboardTests(TestCase):
    def test_home_renders_counts(self):
        user = make_user("homeuser")
        make_product(user)
        self.client.force_login(user)
        r = self.client.get(reverse("dashboard:home"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["stats"]["listings"], 1)
