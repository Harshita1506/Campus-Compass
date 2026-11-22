from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from locator.models import Building, Department, Room
from tests.helpers import make_user


class LocatorApiTests(TestCase):
    def setUp(self):
        self.b = Building.objects.create(name="Demo Block", code="DB", building_type="academic",
                                         latitude=Decimal("10.000000"), longitude=Decimal("20.000000"), floors=3)
        lib = Building.objects.create(name="Demo Library", code="LB", building_type="library",
                                      latitude=Decimal("10.001"), longitude=Decimal("20.001"))
        dept = Department.objects.create(name="Computer Science", code="CS", building=self.b)
        Room.objects.create(building=self.b, room_number="B204", name="AI Lab", room_type="lab", floor=2,
                            department=dept)
        Room.objects.create(building=self.b, room_number="B310", room_type="cabin", floor=3,
                            faculty_name="Dr. Example Person")
        Room.objects.create(building=lib, room_number="L1", name="Reading Hall", room_type="library")
        self.client.force_login(make_user("explorer"))

    def search(self, **params):
        return self.client.get(reverse("locator:api_search"), params).json()

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("locator:api_search")).status_code, 302)

    def test_buildings_endpoint(self):
        data = self.client.get(reverse("locator:api_buildings")).json()
        self.assertEqual(len(data["buildings"]), 2)
        self.assertEqual(data["buildings"][0]["lat"], 10.0)

    def test_search_room_number(self):
        data = self.search(q="B204")
        self.assertEqual(data["rooms"][0]["name"], "AI Lab")
        self.assertEqual(data["rooms"][0]["floor"], 2)
        self.assertEqual(data["rooms"][0]["department"], "Computer Science")
        self.assertEqual(data["rooms"][0]["building"]["code"], "DB")

    def test_search_faculty(self):
        self.assertEqual(self.search(q="example person")["rooms"][0]["room_number"], "B310")

    def test_search_department_returns_building(self):
        data = self.search(q="computer science")
        self.assertEqual(data["buildings"][0]["code"], "DB")

    def test_filter_by_type(self):
        data = self.search(type="cabin")
        self.assertEqual(len(data["rooms"]), 1)
        self.assertEqual(data["buildings"], [])
        data = self.search(type="library")
        self.assertEqual(data["buildings"][0]["code"], "LB")

    def test_room_unique_per_building(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Room.objects.create(building=self.b, room_number="B204")

    def test_floor_label(self):
        self.assertEqual(Room(floor=0).floor_label, "Ground floor")
        self.assertEqual(Room(floor=3).floor_label, "3rd floor")
