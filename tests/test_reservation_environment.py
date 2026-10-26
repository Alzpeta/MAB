import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import source.reservation as mab


def make_customers(count=2):
    return [
        {
            "customer_id": customer_id,
            "discount_affinity": 0.5,
            "time_flexibility": 0.5,
            "restaurant_loyalty": 0.5,
            "perk_affinity": 0.5,
            "urgency": 0.5,
            "requested_hour": 12,
            "group_size": 2,
        }
        for customer_id in range(count)
    ]


def test_reservation_environment_returns_current_customer_and_resets():
    customers = make_customers(2)
    environment = mab.ReservationEnvironment(customers)

    assert environment.get_customer() is customers[0]

    environment.t = 1
    assert environment.get_customer() is customers[1]

    environment.reset()
    assert environment.t == 0
    assert environment.get_customer() is customers[0]


# zmena zacatek
def test_customer_choice_returns_no_choice_for_empty_displayed_options():
    environment = mab.ReservationEnvironment(make_customers(1))

    chosen_arm, reward, evaluated_arms, abandoned = environment.customer_choice([])

    assert chosen_arm is None
    assert reward == 0
    assert evaluated_arms == []
    assert abandoned is False
# zmena konec


# zmena zacatek
def test_customer_choice_returns_first_accepted_arm(monkeypatch):
    displayed_arm_indices = [
        mab.OPTION_NAMES.index("discount_5pct"),
        mab.OPTION_NAMES.index("discount_10pct"),
        mab.OPTION_NAMES.index("discount_15pct"),
    ]
    random_values = iter([0.9, 0.9, 0.1])
    checked_options = []

    def fake_acceptance_probability(customer, option_name):
        checked_options.append(option_name)
        return 0.5

    monkeypatch.setattr(
        mab,
        "compute_acceptance_probability",
        fake_acceptance_probability,
    )
    monkeypatch.setattr(mab.np.random, "rand", lambda: next(random_values))

    environment = mab.ReservationEnvironment(make_customers(1))

    chosen_arm, reward, evaluated_arms, abandoned = environment.customer_choice(
        displayed_arm_indices
    )

    assert chosen_arm == displayed_arm_indices[1]
    assert reward == 1
    assert checked_options == ["discount_5pct", "discount_10pct"]
    assert evaluated_arms == displayed_arm_indices[:2]
    assert abandoned is False
# zmena konec


# zmena zacatek
def test_customer_choice_returns_no_choice_when_all_options_are_rejected(monkeypatch):
    displayed_arm_indices = [
        mab.OPTION_NAMES.index("discount_5pct"),
        mab.OPTION_NAMES.index("discount_10pct"),
    ]

    monkeypatch.setattr(
        mab,
        "compute_acceptance_probability",
        lambda customer, option_name: 0.5,
    )
    monkeypatch.setattr(mab.np.random, "rand", lambda: 0.9)

    environment = mab.ReservationEnvironment(make_customers(1))

    chosen_arm, reward, evaluated_arms, abandoned = environment.customer_choice(
        displayed_arm_indices
    )

    assert chosen_arm is None
    assert reward == 0
    assert evaluated_arms == displayed_arm_indices
    assert abandoned is False
# zmena konec


# zmena zacatek
def test_customer_choice_abandons_after_a_rejected_offer(monkeypatch):
    displayed_arm_indices = [
        mab.OPTION_NAMES.index("discount_5pct"),
        mab.OPTION_NAMES.index("discount_10pct"),
    ]
    monkeypatch.setitem(mab.CONFIG, "ABANDONMENT_PROBABILITY", 1.0)
    monkeypatch.setattr(
        mab,
        "compute_acceptance_probability",
        lambda customer, option_name: 0.5,
    )
    random_values = iter([0.9, 0.0])
    monkeypatch.setattr(mab.np.random, "rand", lambda: next(random_values))

    environment = mab.ReservationEnvironment(make_customers(1))

    chosen_arm, reward, evaluated_arms, abandoned = environment.customer_choice(
        displayed_arm_indices
    )

    assert chosen_arm is None
    assert reward == 0
    assert evaluated_arms == [displayed_arm_indices[0]]
    assert abandoned is True
# zmena konec


def test_outcome_seed_is_independent_of_global_rng_consumption(monkeypatch):
    displayed_arm_indices = [mab.OPTION_NAMES.index("discount_5pct")]
    monkeypatch.setitem(mab.CONFIG, "ABANDONMENT_PROBABILITY", 0)
    monkeypatch.setattr(
        mab,
        "compute_acceptance_probability",
        lambda customer, option_name, rng=None: 0.5,
    )

    first_environment = mab.ReservationEnvironment(
        make_customers(1),
        outcome_seed=123,
    )
    first_result = first_environment.step(displayed_arm_indices)

    np.random.rand(100)

    second_environment = mab.ReservationEnvironment(
        make_customers(1),
        outcome_seed=123,
    )
    second_result = second_environment.step(displayed_arm_indices)

    assert second_result == first_result


# zmena zacatek
def test_step_advances_customer_index_and_marks_done(monkeypatch):
    monkeypatch.setattr(
        mab.ReservationEnvironment,
        "customer_choice",
        lambda self, displayed_arm_indices: (
            displayed_arm_indices[0],
            1,
            [displayed_arm_indices[0]],
            False,
        ),
    )
    environment = mab.ReservationEnvironment(make_customers(2))
    displayed_arm_indices = [mab.OPTION_NAMES.index("discount_5pct")]

    first_result = environment.step(displayed_arm_indices)
    second_result = environment.step(displayed_arm_indices)

    assert first_result == {
        "chosen_arm": displayed_arm_indices[0],
        "reward": 1,
        "evaluated_arms": [displayed_arm_indices[0]],
        "abandoned": False,
        "done": False,
    }
    assert second_result == {
        "chosen_arm": displayed_arm_indices[0],
        "reward": 1,
        "evaluated_arms": [displayed_arm_indices[0]],
        "abandoned": False,
        "done": True,
    }
    assert environment.t == 2
# zmena konec
