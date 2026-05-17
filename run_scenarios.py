from datetime import datetime
from pathlib import Path
import json
import os

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

import mab


SCENARIOS = {
    "all": None,
    "budget": ["budget"],
    "midrange": ["midrange"],
    "premium": ["premium"],
}


def make_output_dir():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("outputs") / f"mab_run_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

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


def option_category(option_name):

    option = mab.ALL_OPTIONS[option_name]
    has_time_shift = option["time_shift"] > 0
    has_discount = option["discount"] > 0
    has_perk = option["perk_value"] > 0

    if has_time_shift and has_discount and has_perk:
        return "time_discount_perk"

    if has_time_shift and has_discount:
        return "time_discount"

    if has_time_shift and has_perk:
        return "time_perk"

    if has_discount:
        return "discount_only"

    if has_perk:
        return "perk_only"

    if has_time_shift:
        return "time_only"

    return "other"


def run_experiment_with_option_stats(agent_class, k, restaurant_tiers=None):

    restaurants = mab.generate_restaurants(restaurant_tiers)
    customers = mab.generate_customers(restaurants)
    env = mab.ReservationEnvironment(customers)
    agent = agent_class(mab.N_ARMS)

    rewards = []
    shown_counts = np.zeros(mab.N_ARMS)
    accepted_counts = np.zeros(mab.N_ARMS)

    env.reset()

    while True:

        customer = env.get_customer()

        available_options = mab.get_available_options(customer)
        available_indices = mab.option_names_to_indices(available_options)

        if len(available_indices) == 0:
            displayed_arms = np.array([])
        else:
            displayed_arms = agent.select_arms(available_indices, k)

        for arm in displayed_arms:
            shown_counts[arm] += 1

        result = env.step(displayed_arms)
        reward = result["reward"]
        rewards.append(reward)

        if result["chosen_arm"] is not None:
            accepted_counts[result["chosen_arm"]] += 1
            agent.update(result["chosen_arm"], reward)

        if result["done"]:
            break

    option_rows = []

    for arm_index, option_name in enumerate(mab.OPTION_NAMES):

        shown_count = shown_counts[arm_index]
        accepted_count = accepted_counts[arm_index]

        if shown_count == 0:
            acceptance_rate = np.nan
        else:
            acceptance_rate = accepted_count / shown_count

        option_rows.append({
            "option_name": option_name,
            "option_category": option_category(option_name),
            "shown_count": shown_count,
            "accepted_count": accepted_count,
            "acceptance_rate": acceptance_rate,
        })

    return np.mean(rewards), pd.DataFrame(option_rows)


def run_scenario(scenario_name, restaurant_tiers):

    np.random.seed(mab.CONFIG["SEED"])

    restaurants = mab.generate_restaurants(restaurant_tiers)
    customers = mab.generate_customers(restaurants)

    np.random.seed(mab.CONFIG["SEED"])

    all_results = []
    all_option_results = []

    for k in mab.CONFIG["N_SHOWN_OPTIONS_LIST"]:

        print("\n" + "=" * 60)
        print(f"SCENARIO = {scenario_name} | TOP-K = {k}")
        print("=" * 60)

        topk_rows = []

        for agent_name, agent_class in mab.AGENTS.items():

            run_rewards = []
            run_option_results = []

            for run in range(mab.CONFIG["N_RUNS"]):

                mean_reward, option_stats_df = run_experiment_with_option_stats(
                    agent_class,
                    k,
                    restaurant_tiers=restaurant_tiers
                )

                run_rewards.append(mean_reward)
                option_stats_df["run"] = run
                run_option_results.append(option_stats_df)

            option_results_df = pd.concat(
                run_option_results,
                ignore_index=True
            )

            option_summary_df = (
                option_results_df
                .groupby(["option_name", "option_category"], as_index=False)
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
            option_summary_df["scenario"] = scenario_name
            option_summary_df["restaurant_tiers"] = (
                "all"
                if restaurant_tiers is None
                else ", ".join(restaurant_tiers)
            )
            option_summary_df["agent"] = agent_name
            option_summary_df["top_k"] = k

            all_option_results.append(option_summary_df)

            mean_reward = np.mean(run_rewards)
            std_reward = np.std(run_rewards)

            row = {
                "scenario": scenario_name,
                "restaurant_tiers": (
                    "all"
                    if restaurant_tiers is None
                    else ", ".join(restaurant_tiers)
                ),
                "agent": agent_name,
                "top_k": k,
                "mean_reward": mean_reward,
                "std_reward": std_reward,
                "ci95": 1.96 * std_reward / np.sqrt(mab.CONFIG["N_RUNS"]),
                "min_reward": np.min(run_rewards),
                "max_reward": np.max(run_rewards),
            }

            topk_rows.append(row)

        random_reward = next(
            row["mean_reward"]
            for row in topk_rows
            if row["agent"] == "Random"
        )

        for row in topk_rows:

            if random_reward == 0:
                row["improvement_vs_random_pct"] = np.nan
            else:
                row["improvement_vs_random_pct"] = (
                    (row["mean_reward"] - random_reward)
                    / random_reward
                ) * 100

        topk_rows = sorted(
            topk_rows,
            key=lambda x: x["mean_reward"],
            reverse=True
        )

        for rank, row in enumerate(topk_rows, start=1):

            row["rank"] = rank
            all_results.append(row)

            print(
                f"{rank}. "
                f"{row['agent']:<20}"
                f"reward={row['mean_reward']:.4f} | "
                f"std={row['std_reward']:.4f} | "
                f"CI95=+/-{row['ci95']:.4f} | "
                f"improvement={row['improvement_vs_random_pct']:+.2f}%"
            )

    return (
        pd.DataFrame(all_results),
        pd.concat(all_option_results, ignore_index=True),
        restaurants_to_dataframe(restaurants),
        customers_to_dataframe(customers),
    )


def save_config(output_dir):

    config_output = {
        "config": mab.CONFIG,
        "scenarios": SCENARIOS,
        "agents": list(mab.AGENTS.keys()),
        "options": mab.ALL_OPTIONS,
        "restaurant_configs": mab.RESTAURANT_CONFIGS,
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
            mab.CONFIG["OPEN_HOUR"],
            mab.CONFIG["CLOSE_HOUR"] + 1
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


def main():

    output_dir = make_output_dir()
    save_config(output_dir)

    scenario_results = []
    scenario_option_results = []

    for scenario_name, restaurant_tiers in SCENARIOS.items():

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


if __name__ == "__main__":
    main()
