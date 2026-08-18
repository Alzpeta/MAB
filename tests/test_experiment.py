import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import source.experiment as mab
from source.options import OPTION_NAMES


# zmena zacatek
def test_position_metrics_only_count_offers_evaluated_before_abandonment(
    monkeypatch,
):
    first_option = "discount_5pct"
    second_option = "discount_10pct"

    class StaticAgent:

        def __init__(self, n_arms):
            self.updated_arms = []

        def select_arms(self, available_indices, k):
            return available_indices[:k]

        def update(self, arm, reward):
            self.updated_arms.append((arm, reward))

    class AbandonmentEnvironment:

        def __init__(self, customers):
            self.customers = customers

        def reset(self):
            pass

        def get_customer(self):
            return self.customers[0]

        def step(self, displayed_arm_indices):
            return {
                "chosen_arm": None,
                "reward": 0,
                "evaluated_arms": [displayed_arm_indices[0]],
                "abandoned": True,
                "done": True,
            }

    monkeypatch.setattr(mab, "ReservationEnvironment", AbandonmentEnvironment)
    monkeypatch.setattr(
        mab,
        "get_available_options",
        lambda customer: [first_option, second_option],
    )

    _, option_stats_df, position_stats_df = mab.run_experiment_with_option_stats(
        StaticAgent,
        k=2,
        customers=[{}],
    )

    first_arm_row = option_stats_df.loc[
        option_stats_df["option_name"] == first_option
    ].iloc[0]
    second_arm_row = option_stats_df.loc[
        option_stats_df["option_name"] == second_option
    ].iloc[0]
    first_position = position_stats_df.loc[
        position_stats_df["position"] == 1
    ].iloc[0]
    second_position = position_stats_df.loc[
        position_stats_df["position"] == 2
    ].iloc[0]

    assert first_arm_row["examined_count"] == 1
    assert second_arm_row["examined_count"] == 0
    assert first_position["position_examined_count"] == 1
    assert first_position["position_acceptance_rate"] == 0
    assert first_position["abandoned_after_position_count"] == 1
    assert second_position["position_examined_count"] == 0
    assert np.isnan(second_position["position_acceptance_rate"])
    assert second_position["abandoned_after_position_count"] == 0
# zmena konec
