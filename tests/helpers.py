"""Shared factories for tests (fictional users only)."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model

PASSWORD = "Str0ng!Pass#2026"


def make_user(username, role="student", verified=True, **extra):
    User = get_user_model()
    return User.objects.create_user(username=username, email=f"{username}@example.test", password=PASSWORD,
                                    first_name=username.title(), role=role, is_email_verified=verified, **extra)


def make_admin(username="boss"):
    User = get_user_model()
    return User.objects.create_superuser(username=username, email=f"{username}@example.test", password=PASSWORD,
                                         role="admin", is_email_verified=True)


def make_product(seller, **kw):
    from marketplace.models import Product
    data = dict(title="Physics textbook", description="Good condition", price=Decimal("300"), category="books",
                condition="good")
    data.update(kw)
    return Product.objects.create(seller=seller, **data)


def make_item(owner, **kw):
    from lostfound.models import Item
    data = dict(item_type="lost", title="Blue water bottle", category="bottles", description="Steel bottle",
                location="Library ground floor", date=date.today())
    data.update(kw)
    return Item.objects.create(owner=owner, **data)
