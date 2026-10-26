import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_scenarios as mab


# zmena zacatek
def test_summarize_confidence_interval_returns_mean_and_bounds():
    mean, ci95, lower, upper = mab.summarize_confidence_interval(
        [0.1, 0.2, 0.3]
    )

    expected_ci95 = 1.96 * 0.1 / math.sqrt(3)

    assert math.isclose(mean, 0.2)
    assert math.isclose(ci95, expected_ci95)
    assert math.isclose(lower, mean - ci95)
    assert math.isclose(upper, mean + ci95)


def test_paired_difference_confidence_interval_uses_matching_runs():
    results_df = pd.DataFrame([
        {
            "scenario": "test",
            "restaurant_tiers": "all",
            "agent": "Candidate",
            "top_k": 1,
        },
    ])
    run_results_df = pd.DataFrame([
        {
            "scenario": "test",
            "restaurant_tiers": "all",
            "agent": "Candidate",
            "top_k": 1,
            "run": 0,
            "reward": 0.5,
        },
        {
            "scenario": "test",
            "restaurant_tiers": "all",
            "agent": "Candidate",
            "top_k": 1,
            "run": 1,
            "reward": 0.7,
        },
        {
            "scenario": "test",
            "restaurant_tiers": "all",
            "agent": "Random",
            "top_k": 1,
            "run": 0,
            "reward": 0.2,
        },
        {
            "scenario": "test",
            "restaurant_tiers": "all",
            "agent": "Random",
            "top_k": 1,
            "run": 1,
            "reward": 0.4,
        },
    ])

    result = mab.add_paired_difference_confidence_intervals(
        results_df,
        run_results_df,
        "Random",
        "vs_random",
    ).iloc[0]

    assert math.isclose(result["vs_random_mean_difference"], 0.3)
    assert math.isclose(result["vs_random_ci95"], 0, abs_tol=1e-12)
    assert math.isclose(result["vs_random_ci95_lower"], 0.3)
    assert math.isclose(result["vs_random_ci95_upper"], 0.3)
# zmena konec
