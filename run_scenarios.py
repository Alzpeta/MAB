import argparse
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import json
import sys
import time
import zlib

from source.restaurants import generate_restaurants, RESTAURANT_CONFIGS
from source.customers import generate_customers
from source.agents import AGENTS
from source.experiment import run_experiment_with_option_stats
from source.options import ALL_OPTIONS
from source.config import CONFIG

DEFAULT_CONFIG = deepcopy(CONFIG)
import numpy as np
import pandas as pd

SCENARIOS = {
    "all": None,
    # "budget": ["budget"],
    # "midrange": ["midrange"],
    # "premium": ["premium"],
}

DEFAULT_RUN_CONFIG_OVERRIDES = {
    "N_CUSTOMERS": 2000,
    "N_RUNS": 100,
    "N_SHOWN_OPTIONS_LIST": [3],
    "SEED": 33,
}

REQUESTED_EXPERIMENTS = [
    {
        "name": "baseline",
        "description": "Baseline configuration; evaluate k from 1 to 7.",
        "config_overrides": {},
    },
    # {
    #     "name": "extended_operating_hours",
    #     "description": "Extend opening hours from 11:00-23:00 to 09:00-24:00.",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "OPEN_HOUR": 9,
    #         "CLOSE_HOUR": 24,
    #     },
    # },
    # {
    #     "name": "much_lower_occupancy",
    #     "description": "Use the Much Lower occupancy scenario from the paper.",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1],
    #         "TIER_BASE_OCCUPANCY": {
    #             "budget": 0.15,
    #             "midrange": 0.30,
    #             "premium": 0.45,
    #         },
    #     },
    # },
    # {
    #     "name": "lower_occupancy",
    #     "description": "Use the Lower occupancy scenario from the paper.",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1],
    #         "TIER_BASE_OCCUPANCY": {
    #             "budget": 0.30,
    #             "midrange": 0.45,
    #             "premium": 0.60,
    #         },
    #     },
    # },
    # {
    #     "name": "higher_occupancy",
    #     "description": "Use the Higher occupancy scenario from the paper.",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1],
    #         "TIER_BASE_OCCUPANCY": {
    #             "budget": 0.60,
    #             "midrange": 0.75,
    #             "premium": 0.90,
    #         },
    #     },
    # },
    # {
    #     "name": "much_higher_occupancy",
    #     "description": "Use the Much Higher occupancy scenario from the paper.",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1],
    #         "TIER_BASE_OCCUPANCY": {
    #             "budget": 0.75,
    #             "midrange": 0.90,
    #             "premium": 0.98,
    #         },
    #     },
    # },
    # {
    #     "name": "very_low_decision_uncertainty",
    #     "description": "Use low decision uncertainty (sigma = 0.1).",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "NOISE_STD": 0.1,
    #     },
    # },
    # {
    #     "name": "low_decision_uncertainty",
    #     "description": "Use low decision uncertainty (sigma = 0.1).",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "NOISE_STD": 0.3,
    #     },
    # },
    # {
    #     "name": "high_decision_uncertainty",
    #     "description": "Use high decision uncertainty (sigma = 1.0).",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "NOISE_STD": 1.0,
    #     },
    # },
    # {
    #     "name": "very_high_decision_uncertainty",
    #     "description": "Use very high decision uncertainty (sigma = 1.5).",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "NOISE_STD": 1.5,
    #     },
    # },
    # {
    #     "name": "very_pessimistic_customer_attitude",
    #     "description": "Use very pessimistic customer attitude (U0 = -3.5).",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "BASE_UTILITY": -3.5,
    #     },
    # },
    # {
    #     "name": "pessimistic_customer_attitude",
    #     "description": "Use pessimistic customer attitude (U0 = -2.5).",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "BASE_UTILITY": -2.5,
    #     },
    # },
    # {
    #     "name": "optimistic_customer_attitude",
    #     "description": "Use optimistic customer attitude (U0 = -1.0).",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "BASE_UTILITY": -1.0,
    #     },
    # },
    # {
    #     "name": "very_optimistic_customer_attitude",
    #     "description": "Use very optimistic customer attitude (U0 = 0.0).",
    #     "config_overrides": {
    #         "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    #         "BASE_UTILITY": 0.0,
    #     },
    # },
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run reservation MAB scenarios."
    )
    parser.add_argument(
        "--requested-experiments",
        action="store_true",
        help=(
            "Run all requested experiments from docs/experiments.md "
            "one after another."
        ),
    )

    return parser.parse_args()


def configure_run():
    run_name = f"mab_run_init_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    config_overrides = deepcopy(DEFAULT_RUN_CONFIG_OVERRIDES)
    scenarios = SCENARIOS

    return run_name, config_overrides, scenarios


def apply_config_overrides(config_overrides):
    unknown_keys = sorted(
        key
        for key in config_overrides
        if key not in CONFIG
    )

    if unknown_keys:
        raise KeyError(
            "Unknown CONFIG override(s): "
            + ", ".join(unknown_keys)
        )

    CONFIG.update(config_overrides)
    np.random.seed(CONFIG["SEED"])


def reset_config():
    CONFIG.clear()
    CONFIG.update(deepcopy(DEFAULT_CONFIG))


def format_duration(seconds):
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


def print_progress(label, current, total, start_time):
    elapsed = time.time() - start_time
    progress = current / total if total else 1
    bar_width = 28
    filled_width = int(bar_width * progress)
    bar = "#" * filled_width + "-" * (bar_width - filled_width)
    percent = progress * 100
    runs_per_second = current / elapsed if elapsed > 0 else 0

    if current and runs_per_second:
        eta = (total - current) / runs_per_second
    else:
        eta = 0

    message = (
        f"\r{label} "
        f"[{bar}] "
        f"{current}/{total} "
        f"({percent:5.1f}%) | "
        f"{runs_per_second:.2f} runs/s | "
        f"elapsed {format_duration(elapsed)} | "
        f"eta {format_duration(eta)}"
    )

    sys.stdout.write(message)
    sys.stdout.flush()

    if current >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()


# zmena zacatek
def summarize_confidence_interval(values):
    values = np.asarray(values, dtype=float)
    mean_value = values.mean()

    if len(values) < 2:
        return mean_value, 0.0, mean_value, mean_value

    standard_deviation = values.std(ddof=1)
    ci95 = 1.96 * standard_deviation / np.sqrt(len(values))

    return (
        mean_value,
        ci95,
        mean_value - ci95,
        mean_value + ci95,
    )


def add_paired_difference_confidence_intervals(
    results_df,
    run_results_df,
    baseline_agent,
    column_prefix,
):
    baseline_runs = run_results_df[
        run_results_df["agent"] == baseline_agent
    ]

    for index, row in results_df.iterrows():
        candidate_runs = run_results_df[
            (run_results_df["scenario"] == row["scenario"])
            & (run_results_df["restaurant_tiers"] == row["restaurant_tiers"])
            & (run_results_df["top_k"] == row["top_k"])
            & (run_results_df["agent"] == row["agent"])
        ][["run", "reward"]]
        matching_baseline_runs = baseline_runs[
            (baseline_runs["scenario"] == row["scenario"])
            & (baseline_runs["restaurant_tiers"] == row["restaurant_tiers"])
            & (baseline_runs["top_k"] == row["top_k"])
        ][["run", "reward"]]
        paired_runs = candidate_runs.merge(
            matching_baseline_runs,
            on="run",
            suffixes=("_candidate", "_baseline"),
        )

        if paired_runs.empty:
            mean_difference = np.nan
            ci95 = np.nan
            ci95_lower = np.nan
            ci95_upper = np.nan
        else:
            differences = (
                paired_runs["reward_candidate"]
                - paired_runs["reward_baseline"]
            )
            (
                mean_difference,
                ci95,
                ci95_lower,
                ci95_upper,
            ) = summarize_confidence_interval(differences)

        results_df.loc[index, f"{column_prefix}_mean_difference"] = (
            mean_difference
        )
        results_df.loc[index, f"{column_prefix}_ci95"] = ci95
        results_df.loc[index, f"{column_prefix}_ci95_lower"] = ci95_lower
        results_df.loc[index, f"{column_prefix}_ci95_upper"] = ci95_upper

    return results_df
# zmena konec


def make_output_dir(run_name=None):
    if run_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"mab_run_{timestamp}"

    output_dir = Path("outputs") / run_name

    if output_dir.exists():
        raise FileExistsError(
            f"Output directory already exists: {output_dir}"
        )

    output_dir.mkdir(parents=True)

    return output_dir


def customers_to_dataframe(customers):
    rows = []

    for customer in customers:
        rows.append({
            "customer_id": customer["customer_id"],
            "restaurant_id": customer["restaurant_id"],
            "restaurant_name": customer["restaurant"]["name"],
            "restaurant_tier": customer["restaurant"]["tier"],
            "requested_day": customer["requested_day"],
            "requested_hour": customer["requested_hour"],
            "discount_affinity": customer["discount_affinity"],
            "time_flexibility": customer["time_flexibility"],
            "restaurant_loyalty": customer["restaurant_loyalty"],
            "perk_affinity": customer["perk_affinity"],
            "urgency": customer["urgency"],
            "future_visit_frustration": customer["future_visit_frustration"],
            "group_size": customer["group_size"],
        })

    return pd.DataFrame(rows)


def restaurants_to_dataframe(restaurants):
    rows = []

    for restaurant in restaurants:
        rows.append({
            "restaurant_id": restaurant["restaurant_id"],
            "name": restaurant["name"],
            "tier": restaurant["tier"],
            "allowed_options": ", ".join(restaurant["allowed_options"]),
        })

    return pd.DataFrame(rows)



def run_scenario(scenario_name, restaurant_tiers):
    sample_restaurants = None
    sample_customers = None

    run_result_rows = []
    all_option_results = []
    # zmena zacatek
    all_position_results = []
    # zmena konec

    random_reward_by_k = {}

    for k in CONFIG["N_SHOWN_OPTIONS_LIST"]:

        print("\n" + "=" * 60)
        print(f"SCENARIO = {scenario_name} | TOP-K = {k}")
        print("=" * 60)

        top_k_summary_rows = []

        for agent_name, agent_class in AGENTS.items():

            run_rewards = []
            progress_started_at = time.time()
            progress_label = (
                f"{scenario_name} | top-k={k} | {agent_name:<20}"
            )

            for run in range(CONFIG["N_RUNS"]):
                instance_seed = CONFIG["SEED"] + run
                outcome_seed = CONFIG["SEED"] + 10000 + run
                policy_seed = zlib.crc32(
                    f"{CONFIG['SEED']}:{run}:{agent_name}".encode("utf-8")
                )
                instance_rng = np.random.default_rng(instance_seed)
                agent_rng = np.random.default_rng(policy_seed)

                restaurants = generate_restaurants(
                    restaurant_tiers,
                    rng=instance_rng,
                )
                customers = generate_customers(restaurants, rng=instance_rng)

                if sample_restaurants is None:
                    sample_restaurants = restaurants
                    sample_customers = customers

                (
                    mean_reward,
                    option_stats_df,
                    position_stats_df,
                ) = run_experiment_with_option_stats(
                    agent_class,
                    k,
                    customers,
                    agent_rng=agent_rng,
                    outcome_seed=outcome_seed,
                )

                run_rewards.append(mean_reward)

                run_result_rows.append({
                    "scenario": scenario_name,
                    "restaurant_tiers": (
                        "all"
                        if restaurant_tiers is None
                        else ", ".join(restaurant_tiers)
                    ),
                    "agent": agent_name,
                    "top_k": k,
                    "run": run,
                    "instance_seed": instance_seed,
                    "policy_seed": policy_seed,
                    "outcome_seed": outcome_seed,
                    "reward": mean_reward,
                })

                option_stats_df["scenario"] = scenario_name
                option_stats_df["restaurant_tiers"] = (
                    "all"
                    if restaurant_tiers is None
                    else ", ".join(restaurant_tiers)
                )
                option_stats_df["agent"] = agent_name
                option_stats_df["top_k"] = k
                option_stats_df["run"] = run
                all_option_results.append(option_stats_df)

                # zmena zacatek
                position_stats_df["scenario"] = scenario_name
                position_stats_df["restaurant_tiers"] = (
                    "all"
                    if restaurant_tiers is None
                    else ", ".join(restaurant_tiers)
                )
                position_stats_df["agent"] = agent_name
                position_stats_df["top_k"] = k
                position_stats_df["run"] = run
                all_position_results.append(position_stats_df)
                # zmena konec

                print_progress(
                    progress_label,
                    run + 1,
                    CONFIG["N_RUNS"],
                    progress_started_at
                )

            # zmena zacatek
            (
                mean_reward,
                ci95,
                ci95_lower,
                ci95_upper,
            ) = summarize_confidence_interval(run_rewards)
            std_reward = np.std(run_rewards, ddof=1) if len(run_rewards) > 1 else 0
            # zmena konec

            if agent_name == "Random":
                random_reward_by_k[k] = mean_reward

            random_reward = random_reward_by_k.get(k)
            if random_reward in (None, 0):
                improvement = np.nan
            else:
                improvement = (
                    (mean_reward - random_reward)
                    / random_reward
                ) * 100

            print(
                f"{agent_name:<20}"
                f"reward={mean_reward:.4f} | "
                f"std={std_reward:.4f} | "
                f"CI95=+/-{ci95:.4f} | "
                f"improvement={improvement:+.2f}%"
            )

            top_k_summary_rows.append({
                "agent": agent_name,
                "mean_reward": mean_reward,
                "std_reward": std_reward,
                "ci95": ci95,
                # zmena zacatek
                "ci95_lower": ci95_lower,
                "ci95_upper": ci95_upper,
                # zmena konec
                "improvement_vs_random_pct": improvement,
            })

        random_reward = next(
            row["mean_reward"]
            for row in top_k_summary_rows
            if row["agent"] == "Random"
        )

        for row in top_k_summary_rows:
            if random_reward == 0:
                row["improvement_vs_random_pct"] = np.nan
            else:
                row["improvement_vs_random_pct"] = (
                    (row["mean_reward"] - random_reward)
                    / random_reward
                ) * 100

        top_k_summary_rows = sorted(
            top_k_summary_rows,
            key=lambda row: row["mean_reward"],
            reverse=True
        )

        print("\nRANKING")
        print(
            f"{'rank':>4}  "
            f"{'agent':<20}  "
            f"{'reward':>8}  "
            f"{'std':>8}  "
            f"{'ci95':>8}  "
            f"{'improvement':>12}"
        )
        print("-" * 70)

        for rank, row in enumerate(top_k_summary_rows, start=1):
            improvement = row["improvement_vs_random_pct"]
            improvement_text = (
                ""
                if pd.isna(improvement)
                else f"{improvement:+.2f}%"
            )

            print(
                f"{rank:>4}  "
                f"{row['agent']:<20}  "
                f"{row['mean_reward']:>8.4f}  "
                f"{row['std_reward']:>8.4f}  "
                f"{row['ci95']:>8.4f}  "
                f"{improvement_text:>12}"
            )

    run_results_df = pd.DataFrame(run_result_rows)

    all_results = []

    for (scenario, tiers, agent, top_k), group in run_results_df.groupby(
        ["scenario", "restaurant_tiers", "agent", "top_k"]
    ):
        # zmena zacatek
        (
            mean_reward,
            ci95,
            ci95_lower,
            ci95_upper,
        ) = summarize_confidence_interval(group["reward"])
        # zmena konec
        all_results.append({
            "scenario": scenario,
            "restaurant_tiers": tiers,
            "agent": agent,
            "top_k": top_k,
            "mean_reward": mean_reward,
            # zmena zacatek
            "std_reward": (
                group["reward"].std(ddof=1) if len(group) > 1 else 0
            ),
            "ci95": ci95,
            "ci95_lower": ci95_lower,
            "ci95_upper": ci95_upper,
            # zmena konec
            "min_reward": group["reward"].min(),
            "max_reward": group["reward"].max(),
        })

    results_df = pd.DataFrame(all_results)

    random_rewards = (
        results_df[results_df["agent"] == "Random"]
        .set_index(["scenario", "restaurant_tiers", "top_k"])["mean_reward"]
    )

    for index, row in results_df.iterrows():
        random_reward = random_rewards.loc[
            (row["scenario"], row["restaurant_tiers"], row["top_k"])
        ]
        if random_reward == 0:
            results_df.loc[index, "improvement_vs_random_pct"] = np.nan
        else:
            results_df.loc[index, "improvement_vs_random_pct"] = (
                (row["mean_reward"] - random_reward)
                / random_reward
            ) * 100

    results_df = add_paired_difference_confidence_intervals(
        results_df,
        run_results_df,
        "Random",
        "vs_random",
    )

    results_df = results_df.sort_values(
        ["scenario", "top_k", "mean_reward"],
        ascending=[True, True, False]
    )
    results_df["rank"] = (
        results_df
        .groupby(["scenario", "top_k"])
        .cumcount()
        + 1
    )

    option_results_df = pd.concat(all_option_results, ignore_index=True)
    option_summary_df = (
        option_results_df
        .groupby(
            [
                "scenario",
                "restaurant_tiers",
                "agent",
                "top_k",
                "option_name",
                "option_category",
            ],
            as_index=False
        )
        [["examined_count", "accepted_count"]]
        .sum()
    )
    option_summary_df["acceptance_rate"] = (
        option_summary_df["accepted_count"]
        / option_summary_df["examined_count"]
    )
    option_summary_df["acceptance_rate"] = (
        option_summary_df["acceptance_rate"]
        .replace([np.inf, -np.inf], np.nan)
    )

    # zmena zacatek
    position_results_df = pd.concat(all_position_results, ignore_index=True)
    position_summary_df = (
        position_results_df
        .groupby(
            [
                "scenario",
                "restaurant_tiers",
                "agent",
                "top_k",
                "position",
            ],
            as_index=False
        )
        [[
            "position_examined_count",
            "position_accepted_count",
            "abandoned_after_position_count",
        ]]
        .sum()
    )
    position_summary_df["position_acceptance_rate"] = (
        position_summary_df["position_accepted_count"]
        / position_summary_df["position_examined_count"]
    )
    position_summary_df["position_acceptance_rate"] = (
        position_summary_df["position_acceptance_rate"]
        .replace([np.inf, -np.inf], np.nan)
    )
    # zmena konec

    return (
        results_df,
        option_summary_df,
        restaurants_to_dataframe(sample_restaurants),
        customers_to_dataframe(sample_customers),
        position_summary_df,
        run_results_df,
    )


def save_config(
    output_dir,
    run_name,
    config_overrides,
    scenarios,
    experiment=None
):
    config_output = {
        "run_name": run_name,
        "experiment": experiment,
        "config_overrides": config_overrides,
        "config": CONFIG,
        "scenarios": scenarios,
        "agents": list(AGENTS.keys()),
        "options": ALL_OPTIONS,
        "restaurant_configs": RESTAURANT_CONFIGS,
    }

    with (output_dir / "config_used.json").open("w", encoding="utf-8") as file:
        json.dump(config_output, file, indent=2, ensure_ascii=False)


def run_configured_scenarios(
    run_name,
    config_overrides,
    scenarios,
    experiment=None
):
    reset_config()
    apply_config_overrides(config_overrides)
    output_dir = make_output_dir(run_name)
    save_config(
        output_dir,
        run_name,
        config_overrides,
        scenarios,
        experiment
    )

    scenario_results = []
    scenario_option_results = []
    scenario_position_results = []
    scenario_run_results = []

    for scenario_name, restaurant_tiers in scenarios.items():
        scenario_dir = output_dir / scenario_name
        scenario_dir.mkdir()

        # zmena zacatek
        (
            results_df,
            option_results_df,
            restaurants_df,
            customers_df,
            position_results_df,
            run_results_df,
        ) = run_scenario(
            scenario_name,
            restaurant_tiers
        )
        # zmena konec

        option_category_df = (
            option_results_df
            .groupby(["scenario", "option_category"], as_index=False)
            [["examined_count", "accepted_count"]]
            .sum()
        )
        option_category_df["acceptance_rate"] = (
                option_category_df["accepted_count"]
                / option_category_df["examined_count"]
        )
        option_category_df["acceptance_rate"] = (
            option_category_df["acceptance_rate"]
            .replace([np.inf, -np.inf], np.nan)
        )

        results_df.to_csv(
            scenario_dir / "results.csv",
            index=False
        )
        run_results_df.to_csv(
            scenario_dir / "per_run_results.csv",
            index=False,
        )
        option_results_df.to_csv(
            scenario_dir / "options_detail.csv",
            index=False
        )
        option_category_df.to_csv(
            scenario_dir / "options_by_category.csv",
            index=False
        )
        # zmena zacatek
        position_results_df.to_csv(
            scenario_dir / "position_metrics.csv",
            index=False
        )
        # zmena konec
        restaurants_df.to_csv(
            scenario_dir / "restaurants.csv",
            index=False
        )
        customers_df.head(200).to_csv(
            scenario_dir / "customer_sample.csv",
            index=False
        )
        customers_df.to_csv(
            scenario_dir / "customers.csv",
            index=False
        )
        customers_df.describe().to_csv(
            scenario_dir / "customer_summary.csv"
        )

        scenario_results.append(results_df)
        scenario_option_results.append(option_results_df)
        scenario_position_results.append(position_results_df)
        scenario_run_results.append(run_results_df)

    all_results_df = pd.concat(scenario_results, ignore_index=True)
    all_option_results_df = pd.concat(
        scenario_option_results,
        ignore_index=True
    )
    all_position_results_df = pd.concat(
        scenario_position_results,
        ignore_index=True
    )
    all_run_results_df = pd.concat(scenario_run_results, ignore_index=True)
    all_results_df.to_csv(output_dir / "all_results.csv", index=False)
    all_option_results_df.to_csv(
        output_dir / "all_options_detail.csv",
        index=False
    )
    all_position_results_df.to_csv(
        output_dir / "all_position_metrics.csv",
        index=False
    )
    all_run_results_df.to_csv(
        output_dir / "all_per_run_results.csv",
        index=False,
    )

    print("\nDONE")
    print(f"Outputs saved to: {output_dir.resolve()}")

    return output_dir


def requested_experiment_runs():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for experiment in REQUESTED_EXPERIMENTS:
        config_overrides = deepcopy(DEFAULT_RUN_CONFIG_OVERRIDES)
        config_overrides.update(deepcopy(experiment["config_overrides"]))

        yield {
            "run_name": (
                f"mab_requested_experiments_"
                f"{timestamp}_{experiment['name']}"
            ),
            "experiment": experiment,
            "config_overrides": config_overrides,
            "scenarios": SCENARIOS,
        }


def run_requested_experiments():
    runs = list(requested_experiment_runs())
    output_dirs = []

    for index, run in enumerate(runs, start=1):
        experiment = run["experiment"]

        print("\n" + "#" * 72)
        print(
            f"REQUESTED EXPERIMENT {index}/{len(runs)}: "
            f"{experiment['name']}"
        )
        print(experiment["description"])
        print("#" * 72)

        output_dir = run_configured_scenarios(
            run["run_name"],
            run["config_overrides"],
            run["scenarios"],
            experiment,
        )
        output_dirs.append(output_dir)

    print("\nALL REQUESTED EXPERIMENTS DONE")
    for output_dir in output_dirs:
        print(f"- {output_dir.resolve()}")


def main():
    args = parse_args()

    if args.requested_experiments:
        run_requested_experiments()
        return

    run_name, config_overrides, scenarios = configure_run()
    run_configured_scenarios(run_name, config_overrides, scenarios)


if __name__ == "__main__":
    main()
