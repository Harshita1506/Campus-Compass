"""
Seed the database with FICTIONAL demonstration data.

    python manage.py seed_data          # (re)create all demo data
    python manage.py seed_data --clear  # remove demo data only

All people, emails and campus locations are invented. Demo accounts use the
@campuscompass.demo domain and the password documented in README.md.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from announcements.models import Announcement
from locator.models import Building, Department, Room
from lostfound.matching import record_matches
from lostfound.models import Item
from marketplace.models import Enquiry, Product, ProductReport, SavedProduct
from mentorship.models import MentorshipRequest, SeniorProfile, Skill
from messaging.services import send_message
from roommates.models import RoommateProfile, RoommateRequest

User = get_user_model()
DEMO_DOMAIN = "campuscompass.demo"
DEMO_PASSWORD = "Demo@12345"
ADMIN_PASSWORD = "Admin@12345"

STUDENTS = [
    ("aarav.demo", "Aarav", "Mehta", "CSE", 2), ("diya.demo", "Diya", "Kapoor", "CSE", 2),
    ("kabir.demo", "Kabir", "Nair", "ECE", 3), ("isha.demo", "Isha", "Reddy", "BBA", 1),
    ("rohan.demo", "Rohan", "Verma", "ME", 2), ("meera.demo", "Meera", "Iyer", "DES", 3),
    ("vivaan.demo", "Vivaan", "Joshi", "CSE", 1), ("ananya.demo", "Ananya", "Das", "BT", 4),
]
SENIORS = [
    ("neha.senior", "Neha", "Sharma", "CSE", 2023, "Software Engineer II", "Northwind Labs (fictional)", "software",
     ["Python", "Django", "System Design", "DSA"], "Resume reviews, DSA prep, backend internships"),
    ("arjun.senior", "Arjun", "Malhotra", "CSE", 2022, "Data Scientist", "Bluefin Analytics (fictional)", "data",
     ["Machine Learning", "Python", "SQL", "Statistics"], "ML projects, Kaggle, research papers"),
    ("priya.senior", "Priya", "Menon", "DES", 2021, "Senior Product Designer", "Pixelcraft Studio (fictional)",
     "design", ["Figma", "UX Research", "Design Systems"], "Portfolio reviews, UX case studies"),
    ("sid.senior", "Siddharth", "Rao", "ECE", 2020, "Founder", "Voltbridge (fictional startup)", "startup",
     ["Entrepreneurship", "Fundraising", "IoT"], "Startup ideas, pitch decks, incubators"),
    ("tanvi.senior", "Tanvi", "Kulkarni", "CSE", 2024, "Blockchain Developer", "ChainForge (fictional)",
     "blockchain", ["Solidity", "Web3", "Cryptography", "JavaScript"], "Smart contracts, hackathons"),
]


class Command(BaseCommand):
    help = "Seed the database with fictional demo data for Campus Compass."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Only remove existing demo data")

    def clear(self):
        User.objects.filter(email__endswith="@" + DEMO_DOMAIN).delete()
        Building.objects.filter(is_demo=True).delete()
        Department.objects.filter(name__endswith="(Demo)").delete()
        Announcement.objects.filter(body__contains="(Fictional demo announcement.)").delete()

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)
        self.clear()
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Demo data removed."))
            return
        now = timezone.now()

        # ---------------------------------------------------------- users
        admin_username = "admin"
        if User.objects.filter(username=admin_username).exists():
            admin_username = "demo_admin"
            self.stdout.write(self.style.WARNING("A user named 'admin' already exists; demo admin is 'demo_admin'."))
        User.objects.create_superuser(
            username=admin_username, email=f"admin@{DEMO_DOMAIN}", password=ADMIN_PASSWORD,
            first_name="Campus", last_name="Admin", role=User.Role.ADMIN, is_email_verified=True)
        students = []
        for i, (username, first, last, branch, year) in enumerate(STUDENTS):
            u = User.objects.create_user(username=username, email=f"{username}@{DEMO_DOMAIN}", password=DEMO_PASSWORD,
                                         first_name=first, last_name=last, is_email_verified=True)
            u.profile.branch, u.profile.academic_year = branch, year
            u.profile.bio = f"{first} is a fictional demo student in {branch}."
            u.profile.linkedin_url = f"https://www.linkedin.com/in/{username.replace('.', '-')}-example"
            u.profile.save()
            User.objects.filter(pk=u.pk).update(date_joined=now - timedelta(days=55 - i * 6))
            students.append(u)
        newbie = User.objects.create_user(username="newbie.demo", email=f"newbie.demo@{DEMO_DOMAIN}",
                                          password=DEMO_PASSWORD, first_name="Nikhil", last_name="Bose")
        User.objects.filter(pk=newbie.pk).update(date_joined=now - timedelta(days=1))

        # ---------------------------------------------------------- seniors & mentorship
        seniors = []
        for i, (username, first, last, branch, grad, desig, company, domain, skills, interests) in enumerate(SENIORS):
            u = User.objects.create_user(username=username, email=f"{username}@{DEMO_DOMAIN}", password=DEMO_PASSWORD,
                                         first_name=first, last_name=last, role=User.Role.SENIOR,
                                         is_email_verified=True)
            u.profile.branch, u.profile.academic_year = branch, 6
            u.profile.save()
            User.objects.filter(pk=u.pk).update(date_joined=now - timedelta(days=50 - i * 8))
            sp = SeniorProfile.objects.create(
                user=u, branch=branch, graduation_year=grad, designation=desig, current_company=company, domain=domain,
                introduction=f"Hi! I'm {first}, a {grad} graduate now working as {desig}. Happy to help juniors "
                             f"navigate college and early careers. (Fictional demo profile.)",
                achievements="Hackathon finalist · Teaching assistant for two semesters · Open-source contributor",
                mentorship_interests=interests,
                linkedin_url=f"https://www.linkedin.com/in/{username.replace('.', '-')}-example",
                github_url=f"https://github.com/{username.replace('.', '-')}-example",
                is_available=(i != 3))
            sp.skills.set([Skill.objects.get_or_create(name=s)[0] for s in skills])
            seniors.append(sp)

        mentorship_data = [
            (students[0], seniors[0], "Backend internship prep", "accepted", "Sure! Let's do a call this weekend."),
            (students[1], seniors[0], "DSA roadmap", "pending", ""),
            (students[2], seniors[1], "Getting started with ML", "accepted", "Happy to help — share your projects."),
            (students[5], seniors[2], "Design portfolio review", "pending", ""),
            (students[6], seniors[4], "Learning Solidity", "rejected", "Fully booked this month, try again later."),
            (students[3], seniors[1], "Analytics career path", "pending", ""),
        ]
        for student, senior, topic, status, note in mentorship_data:
            MentorshipRequest.objects.create(student=student, senior=senior, topic=topic, status=status,
                                             message=f"Hi {senior.user.first_name}, I'd love your guidance on {topic.lower()}.",
                                             response_note=note, responded_at=now if status != "pending" else None)

        # ---------------------------------------------------------- campus locator (fictional)
        lat0, lng0 = settings.CAMPUS_CENTER_LAT, settings.CAMPUS_CENTER_LNG

        def pos(dlat, dlng):
            return Decimal(f"{lat0 + dlat:.6f}"), Decimal(f"{lng0 + dlng:.6f}")

        b_specs = [
            ("Aryabhata Academic Block", "A-BLK", "academic", 5, (0.0008, -0.0012), "Lecture halls and CSE/ECE departments", "8:00 AM – 6:00 PM"),
            ("Raman Science & Lab Complex", "L-BLK", "lab", 4, (0.0011, 0.0006), "Computer, electronics and physics labs", "8:00 AM – 8:00 PM"),
            ("Saraswati Central Library", "LIB", "library", 3, (-0.0002, 0.0001), "Reading halls, digital library and group rooms", "8:00 AM – 11:00 PM"),
            ("Annapurna Food Court", "CAF", "cafeteria", 1, (-0.0010, -0.0006), "Main cafeteria, juice bar and snacks", "7:30 AM – 10:30 PM"),
            ("Chanakya Management Block", "M-BLK", "academic", 4, (-0.0006, 0.0015), "School of Business and Law", "8:00 AM – 6:00 PM"),
            ("Admin & Student Services", "ADM", "admin", 2, (0.0001, -0.0020), "Registrar, accounts and student welfare", "9:30 AM – 5:30 PM"),
            ("Kalpana Girls Hostel", "H-K", "hostel", 6, (-0.0018, 0.0012), "Residential block", "24 × 7"),
            ("Vikram Boys Hostel", "H-V", "hostel", 6, (-0.0019, -0.0016), "Residential block", "24 × 7"),
            ("Dhyan Chand Sports Complex", "SPT", "sports", 2, (0.0019, -0.0004), "Indoor courts, gym and track", "6:00 AM – 9:00 PM"),
            ("Tagore Auditorium", "AUD", "auditorium", 2, (0.0003, 0.0021), "800-seat auditorium for events", "As per events"),
        ]
        bld = {}
        for name, code, btype, floors, (dlat, dlng), desc, hours in b_specs:
            lat, lng = pos(dlat, dlng)
            bld[code] = Building.objects.create(name=name + " (Demo)", code=code, building_type=btype, floors=floors,
                                                latitude=lat, longitude=lng, description=desc, opening_hours=hours,
                                                is_demo=True)
        depts = {
            "CSE": Department.objects.create(name="Computer Science & Engineering (Demo)", code="CSE", building=bld["A-BLK"]),
            "ECE": Department.objects.create(name="Electronics & Communication (Demo)", code="ECE", building=bld["A-BLK"]),
            "PHY": Department.objects.create(name="Applied Physics (Demo)", code="PHY", building=bld["L-BLK"]),
            "BBA": Department.objects.create(name="School of Business (Demo)", code="SOB", building=bld["M-BLK"]),
            "LAW": Department.objects.create(name="School of Law (Demo)", code="LAW", building=bld["M-BLK"]),
        }
        rooms = [
            ("A-BLK", "A101", "Lecture Hall 1", "classroom", 1, "CSE", "", 120),
            ("A-BLK", "A102", "Lecture Hall 2", "classroom", 1, "CSE", "", 90),
            ("A-BLK", "A204", "Tutorial Room", "classroom", 2, "ECE", "", 40),
            ("A-BLK", "A305", "Seminar Hall", "seminar", 3, "CSE", "", 200),
            ("A-BLK", "A310", "Faculty Cabin", "cabin", 3, "CSE", "Dr. Kavita Rao (fictional)", None),
            ("A-BLK", "A311", "Faculty Cabin", "cabin", 3, "CSE", "Prof. Manish Gupta (fictional)", None),
            ("A-BLK", "A312", "Faculty Cabin", "cabin", 3, "ECE", "Dr. Farah Khan (fictional)", None),
            ("A-BLK", "A401", "HOD Office – CSE", "office", 4, "CSE", "Prof. R. Subramanian (fictional)", None),
            ("L-BLK", "L001", "AI & ML Lab", "lab", 0, "CSE", "", 60),
            ("L-BLK", "L002", "Blockchain Lab", "lab", 0, "CSE", "", 40),
            ("L-BLK", "L105", "Embedded Systems Lab", "lab", 1, "ECE", "", 45),
            ("L-BLK", "L110", "Physics Lab", "lab", 1, "PHY", "", 50),
            ("L-BLK", "L210", "Faculty Cabin", "cabin", 2, "PHY", "Dr. Sunil Mathur (fictional)", None),
            ("L-BLK", "L301", "Networks Lab", "lab", 3, "CSE", "", 50),
            ("LIB", "G01", "Main Reading Hall", "library", 0, None, "", 300),
            ("LIB", "F12", "Digital Library", "library", 1, None, "", 80),
            ("LIB", "S05", "Group Discussion Room", "library", 2, None, "", 12),
            ("CAF", "C01", "Main Cafeteria", "cafeteria", 0, None, "", 400),
            ("CAF", "C02", "Juice & Coffee Bar", "cafeteria", 0, None, "", 60),
            ("M-BLK", "M201", "Case Study Room", "classroom", 2, "BBA", "", 70),
            ("M-BLK", "M305", "Moot Court", "seminar", 3, "LAW", "", 100),
            ("M-BLK", "M310", "Faculty Cabin", "cabin", 3, "BBA", "Dr. Anjali Sen (fictional)", None),
            ("ADM", "AD10", "Registrar Office", "office", 1, None, "", None),
            ("ADM", "AD12", "Student Welfare Office", "office", 1, None, "", None),
            ("AUD", "AU1", "Main Auditorium", "seminar", 0, None, "", 800),
        ]
        for code, num, name, rtype, floor, dept, faculty, cap in rooms:
            Room.objects.create(building=bld[code], room_number=num, name=name, room_type=rtype, floor=floor,
                                department=depts.get(dept) if dept else None, faculty_name=faculty, capacity=cap)

        # ---------------------------------------------------------- marketplace
        products = [
            (0, "Engineering Mathematics – B.S. Grewal", "books", "good", 350, "available"),
            (1, "Casio fx-991ES Plus calculator", "electronics", "like_new", 700, "available"),
            (2, "Hero Sprint geared cycle", "cycles", "good", 4500, "reserved"),
            (3, "Study table with drawer", "furniture", "fair", 1200, "available"),
            (4, "Mechanical keyboard (blue switches)", "electronics", "like_new", 1800, "available"),
            (5, "Drafter & engineering drawing kit", "stationery", "good", 400, "sold"),
            (6, "Badminton racket – Yonex", "sports", "good", 900, "available"),
            (7, "Electric kettle 1.5L", "hostel", "like_new", 550, "available"),
            (0, "Data Structures notes (handwritten)", "books", "good", 150, "available"),
            (1, "Lab coat – size M", "clothing", "good", 250, "sold"),
            (2, "Arduino Uno starter kit", "electronics", "new", 1500, "available"),
            (3, "Table lamp (LED)", "hostel", "good", 300, "available"),
            (4, "Clean Code – Robert C. Martin", "books", "like_new", 450, "available"),
            (5, "Yoga mat", "sports", "new", 400, "available"),
            (6, "Mini fridge 50L", "hostel", "good", 5200, "sold"),
            (7, "Bluetooth headphones", "electronics", "fair", 800, "available"),
        ]
        product_objs = []
        for i, (si, title, cat, cond, price, status) in enumerate(products):
            p = Product.objects.create(seller=students[si], title=title, category=cat, condition=cond,
                                       price=Decimal(price), status=status,
                                       sold_at=now if status == "sold" else None,
                                       description=f"{title} in {cond.replace('_', ' ')} condition. Pick up on campus. "
                                                   "Fictional demo listing.")
            Product.objects.filter(pk=p.pk).update(created_at=now - timedelta(days=30 - i))
            product_objs.append(p)
        for u, idx in [(students[0], 1), (students[0], 4), (students[1], 0), (students[2], 7), (students[3], 10)]:
            SavedProduct.objects.create(user=u, product=product_objs[idx])
        Enquiry.objects.create(product=product_objs[1], buyer=students[0], message="Is the calculator still available?",
                               offered_price=Decimal(650))
        send_message(students[0], students[1], "Hi Diya! Is the Casio calculator still available? I can offer ₹650.",
                     subject=product_objs[1].title)
        send_message(students[1], students[0], "Hi Aarav, yes it is! Can you meet at the library tomorrow at 5?")
        ProductReport.objects.create(product=product_objs[15], reporter=students[0], reason="misleading",
                                     details="Photos look like they are from an online store.")
        ProductReport.objects.create(product=product_objs[6], reporter=students[3], reason="duplicate",
                                     details="Same racket posted twice.")

        # ---------------------------------------------------------- lost & found
        today = timezone.localdate()
        items = [
            (0, "lost", "Black leather wallet", "bags", "Saraswati Central Library – 2nd floor", 3),
            (1, "found", "Black wallet", "bags", "Central Library 2nd floor reading hall", 2),
            (2, "lost", "Student ID card", "id_card", "Annapurna Food Court", 5),
            (3, "found", "ID card – blue lanyard", "id_card", "Food court near juice bar", 4),
            (4, "lost", "Silver water bottle (Milton)", "bottles", "Dhyan Chand Sports Complex", 6),
            (5, "lost", "AirPods case", "electronics", "Aryabhata Academic Block A101", 1),
            (6, "found", "Wireless earbuds case", "electronics", "Academic Block lecture hall A101", 1),
            (7, "found", "Set of hostel keys", "keys", "Vikram Boys Hostel gate", 8),
            (0, "lost", "Grey hoodie", "clothing", "Tagore Auditorium", 12),
            (2, "found", "Scientific calculator", "electronics", "Raman Lab Complex L105", 10),
        ]
        item_objs = []
        for oi, itype, title, cat, loc, days in items:
            item = Item.objects.create(owner=students[oi], item_type=itype, title=title, category=cat, location=loc,
                                       date=today - timedelta(days=days),
                                       description=f"{title}. Reported at {loc}. Fictional demo report.")
            item_objs.append(item)
        item_objs[7].status = Item.Status.RECOVERED
        item_objs[7].recovered_at = now
        item_objs[7].save()
        for item in item_objs:
            record_matches(item)

        # ---------------------------------------------------------- roommates
        rm_specs = [
            (0, "2nd-year CSE, calm and organised", 6000, 9000, "north_gate", "flat", "veg", "early", 3),
            (1, "Looking for a tidy flatmate near North Gate", 7000, 10000, "north_gate", "flat", "veg", "early", 3),
            (2, "Night owl coder, chill vibes", 5000, 8000, "south_gate", "pg", "nonveg", "night", 2),
            (3, "Fresher looking for a hostel buddy", 4000, 6000, "on_campus", "hostel", "egg", "flexible", 2),
            (4, "Gym + football, easy-going", 5500, 8500, "south_gate", "pg", "nonveg", "night", 1),
            (5, "Designer who loves plants", 8000, 12000, "city_centre", "studio", "vegan", "flexible", 3),
            (6, "Quiet first-year, budget friendly", 3500, 5500, "any", "hostel", "any", "early", 2),
        ]
        rm_objs = []
        for si, headline, bmin, bmax, loc, acc, food, sleep, clean in rm_specs:
            rm_objs.append(RoommateProfile.objects.create(
                user=students[si], headline=headline, budget_min=bmin, budget_max=bmax, preferred_location=loc,
                accommodation_type=acc, food_preference=food, sleep_schedule=sleep, cleanliness=clean,
                about="Fictional demo roommate profile.", move_in_date=today + timedelta(days=30)))
        RoommateRequest.objects.create(sender=students[1], receiver=students[0], message="We look like a great match!")
        RoommateRequest.objects.create(sender=students[4], receiver=students[2], message="Want to share a PG?",
                                       status="accepted")
        rm_objs[0].saved_by.add(students[1])

        # ---------------------------------------------------------- announcements
        ann = [
            ("Mid-semester examination schedule released", "exam", None, "", True,
             "The mid-semester exam timetable for all programmes is now available on the student portal. "
             "Please check your seating plan two days before each exam."),
            ("TechNova 2026 — annual tech fest", "event", now + timedelta(days=12), "Tagore Auditorium (Demo)", True,
             "Three days of hackathons, robotics, talks and gaming. Registrations close one week before the fest."),
            ("Campus placement drive: Software roles", "placement", now + timedelta(days=20), "A305 Seminar Hall", False,
             "Eligible final-year students can register for the upcoming placement drive. Bring updated resumes."),
            ("Library extended hours during exams", "academic", None, "", False,
             "The Central Library will remain open until midnight during the examination fortnight."),
            ("Inter-hostel football league", "sports", now + timedelta(days=5), "Dhyan Chand Sports Complex", False,
             "Form your hostel teams and register with the sports office."),
            ("Photography club: weekend photo walk", "club", now - timedelta(days=3), "Main gate", False,
             "Join the photography club for a sunrise photo walk around campus."),
        ]
        for i, (title, cat, edate, venue, pinned, body) in enumerate(ann):
            a = Announcement.objects.create(title=title, category=cat, event_date=edate, venue=venue, is_pinned=pinned,
                                            body=body + " (Fictional demo announcement.)",
                                            registration_link="https://example.com/register" if edate else "")
            Announcement.objects.filter(pk=a.pk).update(created_at=now - timedelta(days=i * 2))

        self.stdout.write(self.style.SUCCESS(
            f"Demo data created: {User.objects.filter(email__endswith=DEMO_DOMAIN).count()} users, "
            f"{Product.objects.count()} products, {Item.objects.count()} lost/found items, "
            f"{RoommateProfile.objects.count()} roommate profiles, {Building.objects.count()} buildings, "
            f"{Room.objects.count()} rooms, {SeniorProfile.objects.count()} seniors, "
            f"{Announcement.objects.count()} announcements."))
        self.stdout.write(f"Admin login: {admin_username} / {ADMIN_PASSWORD}   Student login: aarav.demo / {DEMO_PASSWORD}")
