import sys
from pathlib import Path

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


def test_customer_choice_returns_no_choice_for_empty_displayed_options():
    environment = mab.ReservationEnvironment(make_customers(1))

    chosen_arm, reward = environment.customer_choice([])

    assert chosen_arm is None
    assert reward == 0


def test_customer_choice_returns_first_accepted_arm(monkeypatch):
    displayed_arm_indices = [
        mab.OPTION_NAMES.index("discount_5pct"),
        mab.OPTION_NAMES.index("discount_10pct"),
        mab.OPTION_NAMES.index("discount_15pct"),
    ]
    random_values = iter([0.9, 0.1])
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

    chosen_arm, reward = environment.customer_choice(displayed_arm_indices)

    assert chosen_arm == displayed_arm_indices[1]
    assert reward == 1
    assert checked_options == ["discount_5pct", "discount_10pct"]


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

    chosen_arm, reward = environment.customer_choice(displayed_arm_indices)

    assert chosen_arm is None
    assert reward == 0


def test_step_advances_customer_index_and_marks_done(monkeypatch):
    monkeypatch.setattr(
        mab.ReservationEnvironment,
        "customer_choice",
        lambda self, displayed_arm_indices: (displayed_arm_indices[0], 1),
    )
    environment = mab.ReservationEnvironment(make_customers(2))
    displayed_arm_indices = [mab.OPTION_NAMES.index("discount_5pct")]

    first_result = environment.step(displayed_arm_indices)
    second_result = environment.step(displayed_arm_indices)

    assert first_result == {
        "chosen_arm": displayed_arm_indices[0],
        "reward": 1,
        "done": False,
    }
    assert second_result == {
        "chosen_arm": displayed_arm_indices[0],
        "reward": 1,
        "done": True,
    }
    assert environment.t == 2
