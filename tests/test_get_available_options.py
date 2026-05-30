import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import source.reservation as mab


def make_restaurant(allowed_options, full_slots=None, occupied_slots=None):
    full_slots = full_slots or set()
    occupied_slots = occupied_slots or {}
    calendar = {}

    for day in range(mab.CONFIG["N_DAYS"]):
        calendar[day] = {}

        for hour in range(mab.CONFIG["OPEN_HOUR"], mab.CONFIG["CLOSE_HOUR"]):
            if (day, hour) in full_slots:
                calendar[day][hour] = mab.CONFIG["SLOTS_PER_HOUR"]
            else:
                calendar[day][hour] = occupied_slots.get((day, hour), 0)

    return {
        "restaurant_id": 1,
        "name": "Test Restaurant",
        "tier": "budget",
        "allowed_options": allowed_options,
        "calendar": calendar,
        "open_hour": mab.CONFIG["OPEN_HOUR"],
        "close_hour": mab.CONFIG["CLOSE_HOUR"],
    }


def make_customer(restaurant, requested_day=0, requested_hour=11, group_size=2):
    return {
        "customer_id": 1,
        "restaurant": restaurant,
        "restaurant_id": restaurant["restaurant_id"],
        "requested_day": requested_day,
        "requested_hour": requested_hour,
        "group_size": group_size,
    }


def test_get_available_options_returns_allowed_options_in_order():
    allowed_options = [
        "discount_5pct",
        "same_day_60min",
        "same_day_120min",
        "same_day_180min",
        "next_day_plus_vip",
    ]
    restaurant = make_restaurant(allowed_options)
    customer = make_customer(restaurant, requested_hour=11)

    assert mab.get_available_options(customer) == allowed_options


def test_get_available_options_filters_full_capacity_and_closed_hours():
    restaurant = make_restaurant(
        [
            "discount_5pct",
            "same_day_60min",
            "same_day_120min",
            "same_day_180min",
            "next_day_plus_vip",
        ],
        full_slots={(0, 22)},
    )
    customer = make_customer(restaurant, requested_day=0, requested_hour=21)

    assert mab.get_available_options(customer) == ["discount_5pct", "next_day_plus_vip"]


def test_get_available_options_allows_option_when_group_size_exactly_fits_capacity():
    restaurant = make_restaurant(
        ["same_day_60min"],
        occupied_slots={(0, 12): mab.CONFIG["SLOTS_PER_HOUR"] - 4},
    )
    customer = make_customer(
        restaurant,
        requested_day=0,
        requested_hour=11,
        group_size=4,
    )

    assert mab.get_available_options(customer) == ["same_day_60min"]


def test_get_available_options_filters_option_when_group_size_exceeds_capacity():
    restaurant = make_restaurant(
        ["same_day_60min"],
        occupied_slots={(0, 12): mab.CONFIG["SLOTS_PER_HOUR"] - 4},
    )
    customer = make_customer(
        restaurant,
        requested_day=0,
        requested_hour=11,
        group_size=5,
    )

    assert mab.get_available_options(customer) == []


def test_get_available_options_filters_all_options_when_group_size_exceeds_total_capacity():
    restaurant = make_restaurant(
        [
            "discount_5pct",
            "same_day_60min",
            "next_day_plus_vip",
        ]
    )
    customer = make_customer(
        restaurant,
        requested_day=0,
        requested_hour=11,
        group_size=mab.CONFIG["SLOTS_PER_HOUR"] + 1,
    )

    assert mab.get_available_options(customer) == []


def test_get_available_options_checks_next_day_capacity_for_group_size():
    restaurant = make_restaurant(
        ["next_day_plus_vip"],
        occupied_slots={(1, 11): mab.CONFIG["SLOTS_PER_HOUR"] - 2},
    )
    customer = make_customer(
        restaurant,
        requested_day=0,
        requested_hour=11,
        group_size=3,
    )

    assert mab.get_available_options(customer) == []
