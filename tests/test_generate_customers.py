import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mab


def setup_function():
    np.random.seed(mab.CONFIG["SEED"])


def test_generate_customers_with_expected_structure():
    restaurants = mab.generate_restaurants()
    customers = mab.generate_customers(restaurants)
    restaurants_by_id = {
        restaurant["restaurant_id"]: restaurant
        for restaurant in restaurants
    }
    affinity_fields = [
        "discount_affinity",
        "time_flexibility",
        "restaurant_loyalty",
        "perk_affinity",
        "urgency",
    ]

    assert len(customers) == mab.CONFIG["N_CUSTOMERS"]

    for expected_customer_id, customer in enumerate(customers):
        assert customer["customer_id"] == expected_customer_id
        assert customer["restaurant_id"] in restaurants_by_id
        assert customer["restaurant"] is restaurants_by_id[customer["restaurant_id"]]

        assert 0 <= customer["requested_day"] < mab.CONFIG["N_DAYS"]
        assert mab.CONFIG["OPEN_HOUR"] <= customer["requested_hour"]
        assert customer["requested_hour"] < mab.CONFIG["CLOSE_HOUR"]

        for field in affinity_fields:
            assert 0 <= customer[field] <= 1

        assert 1 <= customer["group_size"] <= 6
