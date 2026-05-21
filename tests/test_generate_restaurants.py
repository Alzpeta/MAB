import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mab


def setup_function():
    np.random.seed(mab.CONFIG["SEED"])


def print_restaurant_calendar_summary(restaurants):
    hours = list(range(mab.CONFIG["OPEN_HOUR"], mab.CONFIG["CLOSE_HOUR"]))
    header = "restaurant".ljust(25) + "tier".ljust(10)
    header += " | " + " ".join(f"{hour:02d}" for hour in hours)

    print("\nRestaurant calendar occupancy heatmap")
    print("Each cell is the average occupied slots for that hour across all days.")
    print("F = full, # = high occupancy, + = medium, . = low, 0 = empty")
    print(header)
    print("-" * len(header))

    for restaurant in restaurants:
        average_by_hour = []

        for hour in hours:
            occupied_slots = [
                restaurant["calendar"][day][hour]
                for day in range(mab.CONFIG["N_DAYS"])
            ]
            average_by_hour.append(sum(occupied_slots) / len(occupied_slots))

        heatmap = []
        for average_occupied in average_by_hour:
            occupancy_ratio = average_occupied / mab.CONFIG["SLOTS_PER_HOUR"]

            if average_occupied == mab.CONFIG["SLOTS_PER_HOUR"]:
                heatmap.append("F")
            elif average_occupied == 0:
                heatmap.append("0")
            elif occupancy_ratio >= 0.75:
                heatmap.append("#")
            elif occupancy_ratio >= 0.5:
                heatmap.append("+")
            else:
                heatmap.append(".")

        restaurant_label = (
            f"{restaurant['restaurant_id']:02d} {restaurant['name']}"
        ).ljust(25)
        tier_label = restaurant["tier"].ljust(10)

        print(f"{restaurant_label}{tier_label} | {'  '.join(heatmap)}")


def test_generate_all_restaurants_with_expected_structure():
    restaurants = mab.generate_restaurants()

    print_restaurant_calendar_summary(restaurants)

    assert len(restaurants) == mab.CONFIG["N_RESTAURANTS"]

    for restaurant in restaurants:
        config = mab.RESTAURANT_CONFIGS[restaurant["restaurant_id"]]

        assert restaurant["name"] == config["name"]
        assert restaurant["tier"] == config["tier"]
        assert restaurant["allowed_options"] == config["allowed_options"]
        assert restaurant["open_hour"] == mab.CONFIG["OPEN_HOUR"]
        assert restaurant["close_hour"] == mab.CONFIG["CLOSE_HOUR"]
        restaurant["calendar"].pop(7) #fake day removed
        assert set(restaurant["calendar"].keys()) == set(
            range(mab.CONFIG["N_DAYS"])
        )

        for day_calendar in restaurant["calendar"].values():
            assert set(day_calendar.keys()) == set(
                range(
                    mab.CONFIG["OPEN_HOUR"],
                    mab.CONFIG["CLOSE_HOUR"],
                )
            )

            for occupied_slots in day_calendar.values():
                assert isinstance(occupied_slots, int)
                assert occupied_slots >= 0
                assert occupied_slots <= mab.CONFIG["SLOTS_PER_HOUR"]


def test_filters_restaurants_by_tier():
    restaurants = mab.generate_restaurants(["premium"])

    expected_ids = [
        restaurant_id
        for restaurant_id, config in mab.RESTAURANT_CONFIGS.items()
        if config["tier"] == "premium"
    ]

    assert [restaurant["restaurant_id"] for restaurant in restaurants] == expected_ids
    assert all(restaurant["tier"] == "premium" for restaurant in restaurants)
