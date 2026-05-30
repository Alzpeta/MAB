import argparse
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import json
import os
import sys
import time

from source.restaurants import generate_restaurants, RESTAURANT_CONFIGS
from source.customers import generate_customers
from source.agents import AGENTS
from source.experiment import run_experiment_with_option_stats
from source.options import ALL_OPTIONS
from source.config import CONFIG

DEFAULT_CONFIG = deepcopy(CONFIG)

Path("outputs/matplotlib_cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path("outputs/matplotlib_cache").resolve())
)
Path("outputs/cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault(
    "XDG_CACHE_HOME",
    str(Path("outputs/cache").resolve())
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCENARIOS = {
    "all": None,
    # "pro-plebs": ["budget","midrange"],
    "budget": ["budget"],
    "midrange": ["midrange"],
    "premium": ["premium"],
}

DEFAULT_RUN_CONFIG_OVERRIDES = {
    "N_CUSTOMERS": 20000,
    "N_RUNS": 100,
    "N_SHOWN_OPTIONS_LIST": [1, 2, 3],
    "SEED": 33,
}

REQUESTED_EXPERIMENTS = [
    # {
    #     "name": "baseline",
    #     "description": "Use the default configuration.",
    #     "config_overrides": {},
    # },
    {
        "name": "higher_occupancy",
        "description": "Increase TIER_BASE_OCCUPANCY.",
        "config_overrides": {
            "TIER_BASE_OCCUPANCY": {
                "budget": 0.60,
                "midrange": 0.75,
                "premium": 0.90,
            },
        },
    },
    {
        "name": "lower_occupancy",
        "description": "Decrease TIER_BASE_OCCUPANCY.",
        "config_overrides": {
            "TIER_BASE_OCCUPANCY": {
                "budget": 0.30,
                "midrange": 0.45,
                "premium": 0.60,
            },
        },
    },
    {
        "name": "more_optimistic_initial_estimate",
        "description": "Increase INITIAL_ACCEPTANCE_ESTIMATE.",
        "config_overrides": {
            "INITIAL_ACCEPTANCE_ESTIMATE": 0.55,
        },
    },
    {
        "name": "more_positive_customer_mood",
        "description": "Increase BASE_UTILITY.",
        "config_overrides": {
            "BASE_UTILITY": 0,
        },
    },
    {
        "name": "noisy_reward_environment",
        "description": "Increase observation noise in outcomes.",
        "config_overrides": {
            "NOISE_STD": 1,
        },
    },
    {
        "name": "extended_operating_hours",
        "description": "Expand the daily opening window.",
        "config_overrides": {
            "OPEN_HOUR": 13,
            "CLOSE_HOUR": 21,
        },
    },
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
                np.random.seed(CONFIG["SEED"] + run)

                restaurants = generate_restaurants(restaurant_tiers)
                customers = generate_customers(restaurants)

                if sample_restaurants is None:
                    sample_restaurants = restaurants
                    sample_customers = customers

                np.random.seed(CONFIG["SEED"] + 10000 + run)

                mean_reward, option_stats_df = run_experiment_with_option_stats(
                    agent_class,
                    k,
                    customers
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

                print_progress(
                    progress_label,
                    run + 1,
                    CONFIG["N_RUNS"],
                    progress_started_at
                )

            mean_reward = np.mean(run_rewards)
            std_reward = np.std(run_rewards)
            ci95 = 1.96 * std_reward / np.sqrt(CONFIG["N_RUNS"])

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
        rewards = group["reward"]
        all_results.append({
            "scenario": scenario,
            "restaurant_tiers": tiers,
            "agent": agent,
            "top_k": top_k,
            "mean_reward": rewards.mean(),
            "std_reward": rewards.std(ddof=0),
            "ci95": 1.96 * rewards.std(ddof=0) / np.sqrt(CONFIG["N_RUNS"]),
            "min_reward": rewards.min(),
            "max_reward": rewards.max(),
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
        [["shown_count", "accepted_count"]]
        .sum()
    )
    option_summary_df["acceptance_rate"] = (
        option_summary_df["accepted_count"]
        / option_summary_df["shown_count"]
    )
    option_summary_df["acceptance_rate"] = (
        option_summary_df["acceptance_rate"]
        .replace([np.inf, -np.inf], np.nan)
    )

    return (
        results_df,
        option_summary_df,
        restaurants_to_dataframe(sample_restaurants),
        customers_to_dataframe(sample_customers),
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


def save_pretty_table(df, output_path, title):
    display_df = df.copy()

    for column in display_df.columns:

        if pd.api.types.is_float_dtype(display_df[column]):
            display_df[column] = display_df[column].map(
                lambda value: "" if pd.isna(value) else f"{value:.4f}"
            )

    html_table = display_df.to_html(index=False, classes="results-table")

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      color: #222;
    }}
    h1 {{
      font-size: 22px;
      margin-bottom: 16px;
    }}
    table.results-table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
    }}
    .results-table th {{
      background: #263238;
      color: white;
      padding: 8px;
      text-align: left;
      position: sticky;
      top: 0;
    }}
    .results-table td {{
      border-bottom: 1px solid #ddd;
      padding: 7px 8px;
      white-space: nowrap;
    }}
    .results-table tr:nth-child(even) {{
      background: #f6f8fa;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  {html_table}
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")


def draw_heatmap(data, title, output_path, value_format=".3f"):
    fig_width = max(8, len(data.columns) * 1.4)
    fig_height = max(5, len(data.index) * 0.6)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    values = data.to_numpy(dtype=float)
    masked_values = np.ma.masked_invalid(values)

    image = ax.imshow(masked_values, aspect="auto", cmap="viridis")
    ax.set_xticks(np.arange(len(data.columns)))
    ax.set_yticks(np.arange(len(data.index)))
    ax.set_xticklabels(data.columns)
    ax.set_yticklabels(data.index)

    for row_index in range(values.shape[0]):
        for column_index in range(values.shape[1]):

            value = values[row_index, column_index]

            if pd.isna(value):
                label = ""
            else:
                label = format(value, value_format)

            ax.text(
                column_index,
                row_index,
                label,
                ha="center",
                va="center",
                color="white",
                fontsize=9
            )

    ax.set_title(title)
    ax.set_xlabel("TOP-K")
    ax.set_ylabel("Agent")
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_scenario_results(results_df, scenario_name, output_dir):
    plt.figure(figsize=(10, 6))

    for agent_name in results_df["agent"].unique():
        subset = results_df[results_df["agent"] == agent_name]

        plt.plot(
            subset["top_k"],
            subset["mean_reward"],
            marker="o",
            label=agent_name
        )

    plt.xlabel("Number of shown alternatives (TOP-K)")
    plt.ylabel("Mean acceptance reward")
    plt.title(f"Bandit strategy comparison - {scenario_name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_dir / f"{scenario_name}_strategy_comparison.png")
    plt.close()


def plot_result_tables(results_df, scenario_name, output_dir):
    reward_pivot = results_df.pivot(
        index="agent",
        columns="top_k",
        values="mean_reward"
    )
    improvement_pivot = results_df.pivot(
        index="agent",
        columns="top_k",
        values="improvement_vs_random_pct"
    )
    rank_pivot = results_df.pivot(
        index="agent",
        columns="top_k",
        values="rank"
    )

    draw_heatmap(
        reward_pivot,
        f"Mean reward - {scenario_name}",
        output_dir / f"{scenario_name}_mean_reward_heatmap.png"
    )
    draw_heatmap(
        improvement_pivot,
        f"Improvement vs Random (%) - {scenario_name}",
        output_dir / f"{scenario_name}_improvement_heatmap.png",
        value_format=".1f"
    )
    draw_heatmap(
        rank_pivot,
        f"Rank - {scenario_name}",
        output_dir / f"{scenario_name}_rank_heatmap.png",
        value_format=".0f"
    )


def plot_customer_sample(customers_df, scenario_name, output_dir):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    customers_df["requested_hour"].plot(
        kind="hist",
        bins=range(
            CONFIG["OPEN_HOUR"],
            CONFIG["CLOSE_HOUR"] + 1
        ),
        ax=axes[0, 0],
        title="Requested hour"
    )

    customers_df["group_size"].plot(
        kind="hist",
        bins=range(1, 8),
        ax=axes[0, 1],
        title="Group size"
    )

    affinity_columns = [
        "discount_affinity",
        "time_flexibility",
        "restaurant_loyalty",
        "perk_affinity",
        "urgency",
    ]

    customers_df[affinity_columns].mean().plot(
        kind="bar",
        ax=axes[1, 0],
        title="Average customer attributes"
    )

    customers_df["restaurant_tier"].value_counts().plot(
        kind="bar",
        ax=axes[1, 1],
        title="Customers by restaurant tier"
    )

    fig.suptitle(f"Customer sample - {scenario_name}")
    fig.tight_layout()
    fig.savefig(output_dir / f"{scenario_name}_customer_sample.png")
    plt.close(fig)


def plot_option_category_results(option_results_df, scenario_name, output_dir):
    category_df = (
        option_results_df
        .groupby("option_category", as_index=False)
        [["shown_count", "accepted_count"]]
        .sum()
    )
    category_df["acceptance_rate"] = (
            category_df["accepted_count"]
            / category_df["shown_count"]
    )
    category_df["acceptance_rate"] = (
        category_df["acceptance_rate"]
        .replace([np.inf, -np.inf], np.nan)
    )
    category_df = category_df.sort_values(
        "acceptance_rate",
        ascending=False
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].bar(
        category_df["option_category"],
        category_df["acceptance_rate"]
    )
    axes[0].set_title("Acceptance rate by option category")
    axes[0].set_ylabel("Accepted / shown")
    axes[0].tick_params(axis="x", rotation=35)

    axes[1].bar(
        category_df["option_category"],
        category_df["shown_count"]
    )
    axes[1].set_title("Shown count by option category")
    axes[1].set_ylabel("Shown count")
    axes[1].tick_params(axis="x", rotation=35)

    fig.suptitle(f"Option categories - {scenario_name}")
    fig.tight_layout()
    fig.savefig(output_dir / f"{scenario_name}_option_categories.png")
    plt.close(fig)


def plot_top_options(option_results_df, scenario_name, output_dir):
    option_df = (
        option_results_df
        .groupby(["option_name", "option_category"], as_index=False)
        [["shown_count", "accepted_count"]]
        .sum()
    )
    option_df["acceptance_rate"] = (
            option_df["accepted_count"]
            / option_df["shown_count"]
    )
    option_df["acceptance_rate"] = (
        option_df["acceptance_rate"]
        .replace([np.inf, -np.inf], np.nan)
    )
    option_df = option_df[
        option_df["shown_count"] > 0
        ].sort_values(
        ["accepted_count", "acceptance_rate"],
        ascending=False
    ).head(15)

    labels = option_df["option_name"]

    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    axes[0].barh(labels, option_df["accepted_count"])
    axes[0].invert_yaxis()
    axes[0].set_title("Top options by accepted count")
    axes[0].set_xlabel("Accepted count")

    axes[1].barh(labels, option_df["acceptance_rate"])
    axes[1].invert_yaxis()
    axes[1].set_title("Acceptance rate for top options")
    axes[1].set_xlabel("Accepted / shown")

    fig.suptitle(f"Best performing options - {scenario_name}")
    fig.tight_layout()
    fig.savefig(output_dir / f"{scenario_name}_top_options.png")
    plt.close(fig)


def plot_option_agent_heatmap(option_results_df, scenario_name, output_dir):
    category_agent_df = (
        option_results_df
        .groupby(["option_category", "agent"], as_index=False)
        [["shown_count", "accepted_count"]]
        .sum()
    )
    category_agent_df["acceptance_rate"] = (
            category_agent_df["accepted_count"]
            / category_agent_df["shown_count"]
    )
    category_agent_df["acceptance_rate"] = (
        category_agent_df["acceptance_rate"]
        .replace([np.inf, -np.inf], np.nan)
    )

    pivot = category_agent_df.pivot(
        index="option_category",
        columns="agent",
        values="acceptance_rate"
    )

    draw_heatmap(
        pivot,
        f"Option category acceptance by agent - {scenario_name}",
        output_dir / f"{scenario_name}_option_category_agent_heatmap.png"
    )


def plot_overall_comparison(all_results_df, output_dir):
    best_results = (
        all_results_df.sort_values(
            ["scenario", "top_k", "mean_reward"],
            ascending=[True, True, False]
        )
        .groupby(["scenario", "top_k"])
        .head(1)
    )

    labels = (
            best_results["scenario"]
            + " | k="
            + best_results["top_k"].astype(str)
    )

    plt.figure(figsize=(12, 6))
    plt.bar(labels, best_results["mean_reward"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Best mean acceptance reward")
    plt.title("Best result by scenario and TOP-K")
    plt.tight_layout()
    plt.savefig(output_dir / "overall_best_results.png")
    plt.close()


def plot_overall_result_heatmap(all_results_df, output_dir):
    best_by_agent = (
        all_results_df
        .sort_values("mean_reward", ascending=False)
        .groupby(["scenario", "agent"], as_index=False)
        .head(1)
    )

    pivot = best_by_agent.pivot(
        index="scenario",
        columns="agent",
        values="mean_reward"
    )

    draw_heatmap(
        pivot,
        "Best mean reward by scenario and agent",
        output_dir / "overall_best_reward_heatmap.png"
    )


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

    for scenario_name, restaurant_tiers in scenarios.items():
        scenario_dir = output_dir / scenario_name
        scenario_dir.mkdir()

        results_df, option_results_df, restaurants_df, customers_df = run_scenario(
            scenario_name,
            restaurant_tiers
        )

        option_category_df = (
            option_results_df
            .groupby(["scenario", "option_category"], as_index=False)
            [["shown_count", "accepted_count"]]
            .sum()
        )
        option_category_df["acceptance_rate"] = (
                option_category_df["accepted_count"]
                / option_category_df["shown_count"]
        )
        option_category_df["acceptance_rate"] = (
            option_category_df["acceptance_rate"]
            .replace([np.inf, -np.inf], np.nan)
        )

        results_df.to_csv(
            scenario_dir / "results.csv",
            index=False
        )
        option_results_df.to_csv(
            scenario_dir / "options_detail.csv",
            index=False
        )
        option_category_df.to_csv(
            scenario_dir / "options_by_category.csv",
            index=False
        )
        restaurants_df.to_csv(
            scenario_dir / "restaurants.csv",
            index=False
        )
        customers_df.head(200).to_csv(
            scenario_dir / "customer_sample.csv",
            index=False
        )
        customers_df.describe().to_csv(
            scenario_dir / "customer_summary.csv"
        )

        save_pretty_table(
            results_df,
            scenario_dir / "results.html",
            f"Results - {scenario_name}"
        )
        save_pretty_table(
            option_category_df.sort_values(
                "acceptance_rate",
                ascending=False
            ),
            scenario_dir / "options_by_category.html",
            f"Options by category - {scenario_name}"
        )
        save_pretty_table(
            option_results_df.sort_values(
                ["accepted_count", "acceptance_rate"],
                ascending=False
            ),
            scenario_dir / "options_detail.html",
            f"Options detail - {scenario_name}"
        )

        plot_scenario_results(results_df, scenario_name, scenario_dir)
        plot_result_tables(results_df, scenario_name, scenario_dir)
        plot_customer_sample(customers_df, scenario_name, scenario_dir)
        plot_option_category_results(
            option_results_df,
            scenario_name,
            scenario_dir
        )
        plot_top_options(option_results_df, scenario_name, scenario_dir)
        plot_option_agent_heatmap(
            option_results_df,
            scenario_name,
            scenario_dir
        )

        scenario_results.append(results_df)
        scenario_option_results.append(option_results_df)

    all_results_df = pd.concat(scenario_results, ignore_index=True)
    all_option_results_df = pd.concat(
        scenario_option_results,
        ignore_index=True
    )
    all_results_df.to_csv(output_dir / "all_results.csv", index=False)
    all_option_results_df.to_csv(
        output_dir / "all_options_detail.csv",
        index=False
    )
    save_pretty_table(
        all_results_df,
        output_dir / "all_results.html",
        "All scenario results"
    )
    save_pretty_table(
        all_option_results_df.sort_values(
            ["scenario", "accepted_count", "acceptance_rate"],
            ascending=[True, False, False]
        ),
        output_dir / "all_options_detail.html",
        "All option results"
    )
    plot_overall_comparison(all_results_df, output_dir)
    plot_overall_result_heatmap(all_results_df, output_dir)

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
