from .restaurants import generate_restaurants
from .customers import generate_customers
from .reservation import ReservationEnvironment, get_available_options, option_names_to_indices
from .options import N_ARMS, OPTION_NAMES, option_category

import numpy as np
import pandas as pd

def run_experiment(agent_class, k, restaurant_tiers=None):

    restaurants = generate_restaurants(restaurant_tiers)

    customers = generate_customers(restaurants)

    env = ReservationEnvironment(customers)

    agent = agent_class(N_ARMS)

    rewards = []

    env.reset()

    while True:

        customer = env.get_customer()

        available_options = get_available_options(
            customer
        )

        available_indices = option_names_to_indices(
            available_options
        )

        if len(available_indices) == 0:

            displayed_arms = np.array([])

        else:

            displayed_arms = agent.select_arms(
                available_indices,
                k
            )

        result = env.step(displayed_arms)

        reward = result["reward"]

        rewards.append(reward)

        if result["chosen_arm"] is not None:

            agent.update(
                result["chosen_arm"],
                reward
            )

        if result["done"]:
            break

    return np.mean(rewards)


def run_experiment_with_option_stats(agent_class, k, restaurant_tiers=None):

    restaurants = generate_restaurants(restaurant_tiers)
    customers = generate_customers(restaurants)
    env = ReservationEnvironment(customers)
    agent = agent_class(N_ARMS)

    rewards = []
    shown_counts = np.zeros(N_ARMS)
    accepted_counts = np.zeros(N_ARMS)

    env.reset()

    while True:

        customer = env.get_customer()

        available_options = get_available_options(customer)
        available_indices = option_names_to_indices(available_options)

        if len(available_indices) == 0:
            displayed_arms = np.array([])
        else:
            displayed_arms = agent.select_arms(available_indices, k)

        for arm in displayed_arms:
            shown_counts[arm] += 1

        result = env.step(displayed_arms)
        reward = result["reward"]
        rewards.append(reward)

        for arm in displayed_arms:
            reward_for_arm = int(arm == result["chosen_arm"])
            agent.update(arm, reward_for_arm)

        if result["done"]:
            break

    option_rows = []

    for arm_index, option_name in enumerate(OPTION_NAMES):

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
