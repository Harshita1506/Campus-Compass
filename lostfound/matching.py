"""
Potential-match algorithm for Lost & Found.

score = name similarity (40) + category (25) + location (20) + date proximity (15)
Only opposite-type, open items are compared. Matches >= MATCH_THRESHOLD are stored
and both owners are notified once.
"""
import re
from difflib import SequenceMatcher

from django.urls import reverse

from notifications.models import Notification
from notifications.utils import notify

from .models import Item, ItemMatch

MATCH_THRESHOLD = 55
STOPWORDS = {"a", "an", "the", "my", "of", "with", "and", "in", "on", "black", "blue", "red", "white"}


def _tokens(text):
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS and len(t) > 1}


def text_similarity(a, b):
    a, b = a.lower().strip(), b.lower().strip()
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    ta, tb = _tokens(a), _tokens(b)
    jaccard = len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    return max(ratio, jaccard)


def score_pair(item_a, item_b):
    name = text_similarity(item_a.title, item_b.title)
    category = 1.0 if item_a.category == item_b.category else 0.0
    location = text_similarity(item_a.location, item_b.location)
    days = abs((item_a.date - item_b.date).days)
    date = 1.0 if days <= 1 else max(0.0, 1 - (days - 1) / 14)
    total = name * 40 + category * 25 + location * 20 + date * 15
    return round(total)


def find_matches(item, limit=5, threshold=MATCH_THRESHOLD):
    opposite = Item.ItemType.FOUND if item.item_type == Item.ItemType.LOST else Item.ItemType.LOST
    candidates = Item.objects.filter(item_type=opposite, status=Item.Status.OPEN).exclude(owner=item.owner)
    scored = [(c, score_pair(item, c)) for c in candidates]
    scored = [pair for pair in scored if pair[1] >= threshold]
    scored.sort(key=lambda p: p[1], reverse=True)
    return scored[:limit]


def record_matches(item):
    """Store new matches and notify both owners. Returns list of (item, score)."""
    if item.status != Item.Status.OPEN:
        return []
    results = find_matches(item)
    for other, score in results:
        lost, found = (item, other) if item.item_type == Item.ItemType.LOST else (other, item)
        _, created = ItemMatch.objects.get_or_create(lost_item=lost, found_item=found, defaults={"score": score})
        if created:
            notify(lost.owner, Notification.Type.LOSTFOUND_MATCH, "Possible match for your lost item",
                   f"'{found.title}' found at {found.location} looks like your '{lost.title}' ({score}% match).",
                   reverse("lostfound:detail", args=[found.pk]))
            notify(found.owner, Notification.Type.LOSTFOUND_MATCH, "Your found item may belong to someone",
                   f"'{lost.title}' reported lost near {lost.location} ({score}% match).",
                   reverse("lostfound:detail", args=[lost.pk]))
    return results
