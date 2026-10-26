import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_scenarios as mab


def test_configured_run_writes_data_files_without_visual_outputs(
    tmp_path,
    monkeypatch,
):
    output_dir = tmp_path / "test_run"
    monkeypatch.setattr(
        mab,
        "make_output_dir",
        lambda run_name=None: output_dir,
    )

    output_dir.mkdir()
    try:
        result_dir = mab.run_configured_scenarios(
            "test_run",
            {
                "N_CUSTOMERS": 10,
                "N_RUNS": 2,
                "N_SHOWN_OPTIONS_LIST": [1],
                "SEED": 33,
            },
            {"all": None},
        )
    finally:
        mab.reset_config()

    expected_root_files = {
        "all_options_detail.csv",
        "all_per_run_results.csv",
        "all_position_metrics.csv",
        "all_results.csv",
        "config_used.json",
    }
    expected_scenario_files = {
        "customer_sample.csv",
        "customer_summary.csv",
        "customers.csv",
        "options_by_category.csv",
        "options_detail.csv",
        "per_run_results.csv",
        "position_metrics.csv",
        "restaurants.csv",
        "results.csv",
    }

    assert result_dir == output_dir
    assert {path.name for path in output_dir.iterdir() if path.is_file()} == (
        expected_root_files
    )
    assert {path.name for path in (output_dir / "all").iterdir()} == (
        expected_scenario_files
    )
    assert len(pd.read_csv(output_dir / "all" / "customers.csv")) == 10
    assert not list(output_dir.rglob("*.html"))
    assert not list(output_dir.rglob("*.png"))
