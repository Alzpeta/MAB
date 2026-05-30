import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import source.reservation as mab


def make_customer(**overrides):
    customer = {
        "discount_affinity": 0.6,
        "time_flexibility": 0.4,
        "restaurant_loyalty": 0.7,
        "perk_affinity": 0.5,
        "urgency": 0.3,
        "requested_hour": 12,
        "group_size": 2,
    }
    customer.update(overrides)
    return customer


def sigmoid(value):
    return 1 / (1 + math.exp(-value))


def test_compute_acceptance_probability_matches_expected_formula_without_noise(
    monkeypatch,
):
    monkeypatch.setattr(mab.np.random, "normal", lambda mean, std: 0)

    customer = make_customer()
    option_name = "60min_plus_10pct_plus_drink"
    arm = mab.ALL_OPTIONS[option_name]
    normalized_shift = arm["time_shift"] / mab.CONFIG["TIME_SHIFT_NORMALIZER"]

    expected_utility = mab.CONFIG["BASE_UTILITY"]
    expected_utility += (
        customer["discount_affinity"]
        * arm["discount"]
        * mab.CONFIG["DISCOUNT_WEIGHT"]
    )
    expected_utility += (
        (1 - customer["time_flexibility"])
        * (-normalized_shift)
        * mab.CONFIG["TIME_SHIFT_WEIGHT"]
    )
    expected_utility += (
        customer["urgency"]
        * (-normalized_shift)
        * mab.CONFIG["URGENCY_DELAY_WEIGHT"]
    )
    expected_utility += (
        customer["perk_affinity"]
        * arm["perk_value"]
        * mab.CONFIG["PERK_WEIGHT"]
    )
    expected_utility += (
        customer["restaurant_loyalty"]
        * mab.CONFIG["LOYALTY_WEIGHT"]
    )
    expected_probability = sigmoid(expected_utility)

    assert math.isclose(
        mab.compute_acceptance_probability(customer, option_name),
        expected_probability,
    )


def test_compute_acceptance_probability_clips_to_min_probability(monkeypatch):
    monkeypatch.setattr(mab.np.random, "normal", lambda mean, std: 0)
    monkeypatch.setitem(mab.CONFIG, "BASE_UTILITY", -100)

    probability = mab.compute_acceptance_probability(
        make_customer(),
        "same_day_180min",
    )

    assert probability == mab.CONFIG["MIN_ACCEPTANCE_PROBABILITY"]


def test_compute_acceptance_probability_clips_to_max_probability(monkeypatch):
    monkeypatch.setattr(mab.np.random, "normal", lambda mean, std: 0)
    monkeypatch.setitem(mab.CONFIG, "BASE_UTILITY", 100)

    probability = mab.compute_acceptance_probability(
        make_customer(),
        "discount_20pct",
    )

    assert probability == mab.CONFIG["MAX_ACCEPTANCE_PROBABILITY"]


def test_compute_acceptance_probability_penalizes_evening_delay(monkeypatch):
    monkeypatch.setattr(mab.np.random, "normal", lambda mean, std: 0)

    daytime_customer = make_customer(requested_hour=18)
    evening_customer = make_customer(requested_hour=19)

    daytime_probability = mab.compute_acceptance_probability(
        daytime_customer,
        "same_day_180min",
    )
    evening_probability = mab.compute_acceptance_probability(
        evening_customer,
        "same_day_180min",
    )

    assert evening_probability < daytime_probability


def test_compute_acceptance_probability_penalizes_large_group_delay(monkeypatch):
    monkeypatch.setattr(mab.np.random, "normal", lambda mean, std: 0)

    small_group_customer = make_customer(group_size=4)
    large_group_customer = make_customer(group_size=5)

    small_group_probability = mab.compute_acceptance_probability(
        small_group_customer,
        "same_day_180min",
    )
    large_group_probability = mab.compute_acceptance_probability(
        large_group_customer,
        "same_day_180min",
    )

    assert large_group_probability < small_group_probability
