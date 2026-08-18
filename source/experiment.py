from .restaurants import generate_restaurants
from .customers import generate_customers
from .reservation import ReservationEnvironment, get_available_options, option_names_to_indices
from .options import N_ARMS, OPTION_NAMES, option_category

import numpy as np
import pandas as pd

def run_experiment_with_option_stats(
    agent_class,
    k,
    customers,
    agent_rng=None,
    outcome_seed=None,
):


    env = (
        ReservationEnvironment(customers)
        if outcome_seed is None
        else ReservationEnvironment(customers, outcome_seed=outcome_seed)
    )
    agent = (
        agent_class(N_ARMS)
        if agent_rng is None
        else agent_class(N_ARMS, rng=agent_rng)
    )

    rewards = []
    examined_counts = np.zeros(N_ARMS)
    accepted_counts = np.zeros(N_ARMS)
    position_examined_counts = np.zeros(k, dtype=int)
    position_accepted_counts = np.zeros(k, dtype=int)
    abandoned_after_position_counts = np.zeros(k, dtype=int)

    env.reset()

    while True:

        customer = env.get_customer()

        available_options = get_available_options(customer)
        available_indices = option_names_to_indices(available_options)

        if len(available_indices) == 0:
            displayed_arms = np.array([])
        else:
            # for the oracle to see
            if hasattr(agent, "set_customer"):
                agent.set_customer(customer)
            displayed_arms = agent.select_arms(available_indices, k)

        result = env.step(displayed_arms)
        reward = result["reward"]
        rewards.append(reward)

        evaluated_arms = result["evaluated_arms"]
        for position, arm in enumerate(evaluated_arms):
            examined_counts[arm] += 1
            position_examined_counts[position] += 1

        if result["chosen_arm"] is not None:
            accepted_counts[result["chosen_arm"]] += 1
            position_accepted_counts[len(evaluated_arms) - 1] += 1

        if result["abandoned"]:
            abandoned_after_position_counts[len(evaluated_arms) - 1] += 1

        for arm in evaluated_arms:
            if result["chosen_arm"] is None:
                agent.update(arm, 0)
            elif arm == result["chosen_arm"]:
                agent.update(arm, 1)
                break
            else:
                agent.update(arm, 0)
        # zmena konec

        if result["done"]:
            break

    option_rows = []

    for arm_index, option_name in enumerate(OPTION_NAMES):

        examined_count = examined_counts[arm_index]
        accepted_count = accepted_counts[arm_index]

        if examined_count == 0:
            acceptance_rate = np.nan
        else:
            acceptance_rate = accepted_count / examined_count

        option_rows.append({
            "option_name": option_name,
            "option_category": option_category(option_name),
            "examined_count": examined_count,
            "accepted_count": accepted_count,
            "acceptance_rate": acceptance_rate,
        })

    # zmena zacatek
    position_rows = []
    for position in range(k):
        position_examined_count = position_examined_counts[position]
        position_accepted_count = position_accepted_counts[position]
        if position_examined_count == 0:
            position_acceptance_rate = np.nan
        else:
            position_acceptance_rate = (
                position_accepted_count / position_examined_count
            )

        position_rows.append({
            "position": position + 1,
            "position_examined_count": position_examined_count,
            "position_accepted_count": position_accepted_count,
            "position_acceptance_rate": position_acceptance_rate,
            "abandoned_after_position_count": (
                abandoned_after_position_counts[position]
            ),
        })

    return (
        np.mean(rewards),
        pd.DataFrame(option_rows),
        pd.DataFrame(position_rows),
    )
    # zmena konec
