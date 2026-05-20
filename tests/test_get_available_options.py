import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mab


def make_restaurant(allowed_options, full_slots=None):
    full_slots = full_slots or set()
    calendar = {}

    for day in range(mab.CONFIG["N_DAYS"]):
        calendar[day] = {}

        for hour in range(mab.CONFIG["OPEN_HOUR"], mab.CONFIG["CLOSE_HOUR"]):
            calendar[day][hour] = (
                mab.CONFIG["SLOTS_PER_HOUR"]
                if (day, hour) in full_slots
                else 0
            )

    return {
        "restaurant_id": 1,
        "name": "Test Restaurant",
        "tier": "budget",
        "allowed_options": allowed_options,
        "calendar": calendar,
        "open_hour": mab.CONFIG["OPEN_HOUR"],
        "close_hour": mab.CONFIG["CLOSE_HOUR"],
    }


def make_customer(restaurant, requested_day=0, requested_hour=11):
    return {
        "customer_id": 1,
        "restaurant": restaurant,
        "restaurant_id": restaurant["restaurant_id"],
        "requested_day": requested_day,
        "requested_hour": requested_hour,
    }


def test_get_available_options_returns_allowed_options_in_order():
    allowed_options = [
        "discount_5pct",
        "same_day_15min",
        "same_day_60min",
        "same_day_90min",
    ]
    restaurant = make_restaurant(allowed_options)
    customer = make_customer(restaurant, requested_hour=11)

    assert mab.get_available_options(customer) == allowed_options


def test_get_available_options_filters_full_capacity_and_closed_hours():
    restaurant = make_restaurant(
        [
            "discount_5pct",
            "same_day_15min",
            "same_day_60min",
            "same_day_90min",
            "next_day_plus_vip",
        ],
        full_slots={(0, 22)},
    )
    customer = make_customer(restaurant, requested_day=0, requested_hour=21)

    assert mab.get_available_options(customer) == ["discount_5pct"]
