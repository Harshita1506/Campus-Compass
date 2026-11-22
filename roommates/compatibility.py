"""
Roommate compatibility algorithm.

Weights: Budget 30%, Location 25%, Food 15%, Sleep 15%, Cleanliness 15%.
Each factor yields a score in [0, 1]; the weighted sum is returned as a percentage.
"""

WEIGHTS = {"budget": 30, "location": 25, "food": 15, "sleep": 15, "cleanliness": 15}

FOOD_COMPAT = {
    frozenset({"veg", "vegan"}): 0.7,
    frozenset({"veg", "egg"}): 0.6,
    frozenset({"vegan", "egg"}): 0.4,
    frozenset({"egg", "nonveg"}): 0.6,
    frozenset({"veg", "nonveg"}): 0.2,
    frozenset({"vegan", "nonveg"}): 0.1,
}


def budget_score(a_min, a_max, b_min, b_max):
    """Overlap of the two ranges relative to the narrower range."""
    overlap = min(a_max, b_max) - max(a_min, b_min)
    if overlap < 0:
        gap = -overlap
        span = max(a_max - a_min, b_max - b_min, 1)
        return max(0.0, 0.4 - gap / span * 0.4)  # close-but-not-overlapping gets partial credit
    narrower = max(min(a_max - a_min, b_max - b_min), 1)
    return min(1.0, 0.6 + 0.4 * overlap / narrower)


def location_score(a, b):
    if a == b:
        return 1.0
    if "any" in (a, b):
        return 0.7
    return 0.0


def food_score(a, b):
    if a == b:
        return 1.0
    if "any" in (a, b):
        return 0.8
    return FOOD_COMPAT.get(frozenset({a, b}), 0.0)


def sleep_score(a, b):
    if a == b:
        return 1.0
    if "flexible" in (a, b):
        return 0.6
    return 0.0


def cleanliness_score(a, b):
    return {0: 1.0, 1: 0.5}.get(abs(int(a) - int(b)), 0.0)


def compatibility(p1, p2):
    """Return {'score': int, 'breakdown': {...}, 'matching': [labels]} for two RoommateProfiles."""
    factors = {
        "budget": budget_score(p1.budget_min, p1.budget_max, p2.budget_min, p2.budget_max),
        "location": location_score(p1.preferred_location, p2.preferred_location),
        "food": food_score(p1.food_preference, p2.food_preference),
        "sleep": sleep_score(p1.sleep_schedule, p2.sleep_schedule),
        "cleanliness": cleanliness_score(p1.cleanliness, p2.cleanliness),
    }
    total = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
    labels = {"budget": "Budget", "location": "Location", "food": "Food", "sleep": "Sleep schedule",
              "cleanliness": "Cleanliness"}
    matching = [labels[k] for k, v in factors.items() if v >= 0.7]
    breakdown = {k: round(v * WEIGHTS[k], 1) for k, v in factors.items()}
    return {"score": round(total), "breakdown": breakdown, "matching": matching}
