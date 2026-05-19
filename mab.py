# ============================================================
# CONTEXTUAL MULTI-ARMED BANDIT
# RESTAURANT RESERVATION RECOVERY
#
# FULL VERSION
#
# INCLUDED STRATEGIES:
# - Random
# - Epsilon Greedy
# - Decay Epsilon Greedy
# - UCB1
# - Thompson Sampling
# - Softmax
#
# IMPORTANT:
# This environment is HETEROGENEOUS:
# -> users have latent preferences
# -> different users prefer different options
# -> there is NO globally best arm
#
# NOTE:
# Current agents are NON-CONTEXTUAL.
# They do NOT observe latent user preferences.
#
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIG
# ============================================================

CONFIG = {

    # ========================================================
    # EXPERIMENT
    # ========================================================

    "N_CUSTOMERS": 20000,

    "N_RUNS": 100,

    "SEED": 33,

    "N_SHOWN_OPTIONS_LIST": [1,2,3,4,5],

    # ========================================================
    # RESTAURANTS
    # ========================================================

    "N_RESTAURANTS": 15,

    "N_DAYS": 7,

    "OPEN_HOUR": 11,
    "CLOSE_HOUR": 23,

    "SLOTS_PER_HOUR": 20,

    # ========================================================
    # OCCUPANCY DYNAMICS
    # ========================================================

    "EVENING_PEAK_HOURS": [18, 19, 20, 21],

    "EVENING_OCCUPANCY_BOOST": 0.35,

    "WEEKEND_DAYS": [4, 5],

    "WEEKEND_OCCUPANCY_BOOST": 0.25,

    "TIER_BASE_OCCUPANCY": {
            "budget": 0.70,
            "midrange": 0.82,
            "premium": 0.92,
        # "budget": 0.45,
        # "midrange": 0.60,
        # "premium": 0.75,
    },

    # ========================================================
    # BANDIT SETTINGS
    # ========================================================

    "INITIAL_ACCEPTANCE_ESTIMATE": 0.15,

    # ========================================================
    # CUSTOMER DISTRIBUTIONS
    # ========================================================

    "DISCOUNT_AFFINITY_MEAN": 0.5,
    "DISCOUNT_AFFINITY_STD": 0.2,

    "TIME_FLEXIBILITY_MEAN": 0.5,
    "TIME_FLEXIBILITY_STD": 0.2,

    "LOYALTY_MEAN": 0.5,
    "LOYALTY_STD": 0.2,

    "PERK_AFFINITY_MEAN": 0.5,
    "PERK_AFFINITY_STD": 0.2,

    "URGENCY_MEAN": 0.5,
    "URGENCY_STD": 0.25,

    # ========================================================
    # ACCEPTANCE MODEL
    # ========================================================

    "BASE_UTILITY": -2.0,

    "DISCOUNT_WEIGHT": 3.0,

    "TIME_SHIFT_WEIGHT": 2.5,

    "PERK_WEIGHT": 1.0,

    "LOYALTY_WEIGHT": 0.1,

    "URGENCY_DELAY_WEIGHT": 2.0,

    "EVENING_DELAY_PENALTY": 0.7,

    "GROUP_DELAY_PENALTY": 0.7,

    "NOISE_STD": 0.6,

    # ========================================================
    # NORMALIZATION
    # ========================================================

    "TIME_SHIFT_NORMALIZER": 1440,

    # ========================================================
    # ACCEPTANCE PROBABILITY CLIPPING
    # ========================================================

    "MIN_ACCEPTANCE_PROBABILITY": 0.01,
    "MAX_ACCEPTANCE_PROBABILITY": 0.95,
}

np.random.seed(CONFIG["SEED"])


# ============================================================
# OPTION CATALOG
# ============================================================

ALL_OPTIONS = {

    "same_day_15min": {
        "time_shift": 15,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_30min": {
        "time_shift": 30,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_45min": {
        "time_shift": 45,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_60min": {
        "time_shift": 60,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_90min": {
        "time_shift": 90,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_120min": {
        "time_shift": 120,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "next_day_same_time": {
        "time_shift": 1440,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "discount_5pct": {
        "time_shift": 0,
        "discount": 0.05,
        "perk_value": 0.00,
    },

    "discount_10pct": {
        "time_shift": 0,
        "discount": 0.10,
        "perk_value": 0.00,
    },

    "discount_15pct": {
        "time_shift": 0,
        "discount": 0.15,
        "perk_value": 0.00,
    },

    "discount_20pct": {
        "time_shift": 0,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    "free_drink": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.20,
    },

    "free_dessert": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.30,
    },

    "free_appetizer": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.35,
    },

    "vip_table_upgrade": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.45,
    },

    "priority_future_booking": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.10,
    },

    "30min_plus_5pct": {
        "time_shift": 30,
        "discount": 0.05,
        "perk_value": 0.00,
    },

    "45min_plus_10pct": {
        "time_shift": 45,
        "discount": 0.10,
        "perk_value": 0.00,
    },

    "60min_plus_15pct": {
        "time_shift": 60,
        "discount": 0.15,
        "perk_value": 0.00,
    },

    "90min_plus_20pct": {
        "time_shift": 90,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    "30min_plus_drink": {
        "time_shift": 30,
        "discount": 0.00,
        "perk_value": 0.20,
    },

    "60min_plus_dessert": {
        "time_shift": 60,
        "discount": 0.00,
        "perk_value": 0.30,
    },

    "90min_plus_appetizer": {
        "time_shift": 90,
        "discount": 0.00,
        "perk_value": 0.35,
    },

    "next_day_plus_vip": {
        "time_shift": 1440,
        "discount": 0.00,
        "perk_value": 0.45,
    },

    "30min_plus_5pct_plus_drink": {
        "time_shift": 30,
        "discount": 0.05,
        "perk_value": 0.20,
    },

    "60min_plus_10pct_plus_dessert": {
        "time_shift": 60,
        "discount": 0.10,
        "perk_value": 0.30,
    },

    "90min_plus_15pct_plus_vip": {
        "time_shift": 90,
        "discount": 0.15,
        "perk_value": 0.45,
    },
}

OPTION_NAMES = list(ALL_OPTIONS.keys())

N_ARMS = len(OPTION_NAMES)


# ============================================================
# RESTAURANTS
# ============================================================

RESTAURANT_CONFIGS = {

    0: {
        "name": "Lacny Tanier",
        "tier": "budget",
        "allowed_options": [
            "discount_20pct",
            "same_day_30min",
            "same_day_60min",
            "30min_plus_5pct",
            "45min_plus_10pct",
            "30min_plus_drink",
            "60min_plus_10pct_plus_dessert",
        ]
    },

    1: {
        "name": "U Hladneho Vlka",
        "tier": "budget",
        "allowed_options": [
            "discount_15pct",
            "same_day_15min",
            "same_day_45min",
            "30min_plus_5pct_plus_drink",
            "60min_plus_15pct",
            "free_drink",
            "priority_future_booking",
        ]
    },

    2: {
        "name": "Treska & Sen",
        "tier": "budget",
        "allowed_options": [
            "discount_20pct",
            "same_day_30min",
            "same_day_90min",
            "45min_plus_10pct",
            "90min_plus_20pct",
            "free_drink",
            "60min_plus_dessert",
        ]
    },

    3: {
        "name": "Kapustovy Dom",
        "tier": "budget",
        "allowed_options": [
            "discount_15pct",
            "same_day_15min",
            "same_day_60min",
            "30min_plus_5pct",
            "60min_plus_15pct",
            "free_dessert",
            "30min_plus_drink",
        ]
    },

    4: {
        "name": "Rychla Bryndza",
        "tier": "budget",
        "allowed_options": [
            "discount_20pct",
            "same_day_45min",
            "same_day_90min",
            "45min_plus_10pct",
            "90min_plus_20pct",
            "free_appetizer",
            "60min_plus_10pct_plus_dessert",
        ]
    },

    5: {
        "name": "Zlaty Rezen",
        "tier": "midrange",
        "allowed_options": [
            "discount_10pct",
            "same_day_15min",
            "same_day_30min",
            "30min_plus_5pct",
            "60min_plus_dessert",
            "free_dessert",
            "30min_plus_5pct_plus_drink",
        ]
    },

    6: {
        "name": "Knedla u Deda",
        "tier": "midrange",
        "allowed_options": [
            "discount_10pct",
            "same_day_30min",
            "same_day_60min",
            "45min_plus_10pct",
            "30min_plus_drink",
            "free_appetizer",
            "60min_plus_10pct_plus_dessert",
        ]
    },

    7: {
        "name": "Pirohove Nebo",
        "tier": "midrange",
        "allowed_options": [
            "discount_15pct",
            "same_day_15min",
            "same_day_45min",
            "60min_plus_15pct",
            "free_dessert",
            "priority_future_booking",
            "60min_plus_dessert",
        ]
    },

    8: {
        "name": "Haluska Palace",
        "tier": "midrange",
        "allowed_options": [
            "discount_10pct",
            "same_day_30min",
            "same_day_90min",
            "30min_plus_5pct_plus_drink",
            "45min_plus_10pct",
            "free_appetizer",
            "90min_plus_appetizer",
        ]
    },

    9: {
        "name": "Mastny Obrus",
        "tier": "midrange",
        "allowed_options": [
            "discount_15pct",
            "same_day_15min",
            "same_day_60min",
            "30min_plus_drink",
            "60min_plus_dessert",
            "free_dessert",
            "60min_plus_10pct_plus_dessert",
        ]
    },

    10: {
        "name": "Pan Hranolka",
        "tier": "premium",
        "allowed_options": [
            "discount_5pct",
            "same_day_15min",
            "same_day_30min",
            "free_appetizer",
            "vip_table_upgrade",
            "30min_plus_drink",
            "90min_plus_15pct_plus_vip",
        ]
    },

    11: {
        "name": "Grand Bryndza",
        "tier": "premium",
        "allowed_options": [
            "discount_5pct",
            "same_day_15min",
            "same_day_45min",
            "vip_table_upgrade",
            "priority_future_booking",
            "60min_plus_dessert",
            "next_day_plus_vip",
        ]
    },

    12: {
        "name": "Luxusny Gulas",
        "tier": "premium",
        "allowed_options": [
            "discount_10pct",
            "same_day_30min",
            "same_day_60min",
            "free_appetizer",
            "vip_table_upgrade",
            "30min_plus_5pct_plus_drink",
            "90min_plus_15pct_plus_vip",
        ]
    },

    13: {
        "name": "Baron Parok",
        "tier": "premium",
        "allowed_options": [
            "discount_5pct",
            "same_day_15min",
            "same_day_90min",
            "free_dessert",
            "vip_table_upgrade",
            "90min_plus_appetizer",
            "next_day_plus_vip",
        ]
    },

    14: {
        "name": "Kralovsky Langoš",
        "tier": "premium",
        "allowed_options": [
            "discount_10pct",
            "same_day_30min",
            "same_day_60min",
            "free_appetizer",
            "priority_future_booking",
            "60min_plus_dessert",
            "90min_plus_15pct_plus_vip",
        ]
    },
}


# ============================================================
# RESTAURANTS
# ============================================================

def generate_restaurants(restaurant_tiers=None):

    restaurants = []

    restaurant_tiers = (
        set(restaurant_tiers)
        if restaurant_tiers is not None
        else None
    )

    if restaurant_tiers is None:
        restaurant_items = [
            (
                restaurant_id,
                RESTAURANT_CONFIGS[restaurant_id]
            )
            for restaurant_id in range(CONFIG["N_RESTAURANTS"])
        ]
    else:
        restaurant_items = RESTAURANT_CONFIGS.items()

    for restaurant_id, config in restaurant_items:

        if (
            restaurant_tiers is not None
            and config["tier"] not in restaurant_tiers
        ):
            continue

        calendar = {}

        tier = config["tier"]

        for day in range(CONFIG["N_DAYS"]):

            calendar[day] = {}

            for hour in range(
                CONFIG["OPEN_HOUR"],
                CONFIG["CLOSE_HOUR"]
            ):

                base_occupancy = (
                    CONFIG["TIER_BASE_OCCUPANCY"][tier]
                )

                occupancy_ratio = base_occupancy

                if hour in CONFIG["EVENING_PEAK_HOURS"]:

                    occupancy_ratio += (
                        CONFIG["EVENING_OCCUPANCY_BOOST"]
                    )

                if day in CONFIG["WEEKEND_DAYS"]:

                    occupancy_ratio += (
                        CONFIG["WEEKEND_OCCUPANCY_BOOST"]
                    )

                occupancy_ratio += np.random.normal(
                    0,
                    0.08
                )

                occupancy_ratio = np.clip(
                    occupancy_ratio,
                    0.05,
                    0.98
                )

                occupied = int(
                    occupancy_ratio
                    * CONFIG["SLOTS_PER_HOUR"]
                )

                calendar[day][hour] = occupied

        restaurants.append({

            "restaurant_id": restaurant_id,

            "name": config["name"],

            "tier": config["tier"],

            "allowed_options":
                config["allowed_options"],

            "calendar": calendar,

            "open_hour": CONFIG["OPEN_HOUR"],

            "close_hour": CONFIG["CLOSE_HOUR"]
        })

    return restaurants


# ============================================================
# CUSTOMERS
# ============================================================

def generate_customers(restaurants):

    customers = []

    for customer_id in range(CONFIG["N_CUSTOMERS"]):

        restaurant = np.random.choice(restaurants)

        customer = {

            "customer_id": customer_id,

            "restaurant": restaurant,

            "restaurant_id": restaurant["restaurant_id"],

            "requested_day":
                np.random.randint(0, CONFIG["N_DAYS"]),

            "requested_hour":
                np.random.randint(
                    CONFIG["OPEN_HOUR"],
                    CONFIG["CLOSE_HOUR"]
                ),

            "discount_affinity":
                np.clip(
                    np.random.normal(
                        CONFIG["DISCOUNT_AFFINITY_MEAN"],
                        CONFIG["DISCOUNT_AFFINITY_STD"]
                    ),
                    0,
                    1
                ),

            "time_flexibility":
                np.clip(
                    np.random.normal(
                        CONFIG["TIME_FLEXIBILITY_MEAN"],
                        CONFIG["TIME_FLEXIBILITY_STD"]
                    ),
                    0,
                    1
                ),

            "restaurant_loyalty":
                np.clip(
                    np.random.normal(
                        CONFIG["LOYALTY_MEAN"],
                        CONFIG["LOYALTY_STD"]
                    ),
                    0,
                    1
                ),

            "perk_affinity":
                np.clip(
                    np.random.normal(
                        CONFIG["PERK_AFFINITY_MEAN"],
                        CONFIG["PERK_AFFINITY_STD"]
                    ),
                    0,
                    1
                ),

            "urgency":
                np.clip(
                    np.random.normal(
                        CONFIG["URGENCY_MEAN"],
                        CONFIG["URGENCY_STD"]
                    ),
                    0,
                    1
                ),

            "group_size":
                np.random.randint(1, 7)
        }

        customers.append(customer)

    return customers


# ============================================================
# AVAILABILITY
# ============================================================

def has_capacity(restaurant, day, hour):

    return (
        restaurant["calendar"][day][hour]
        < CONFIG["SLOTS_PER_HOUR"]
    )


def get_available_options(customer):

    restaurant = customer["restaurant"]

    day = customer["requested_day"]
    hour = customer["requested_hour"]

    available = []

    for option in restaurant["allowed_options"]:

        arm = ALL_OPTIONS[option]

        future_hour = (
            hour
            + int(np.ceil(arm["time_shift"] / 60))
        )

        if future_hour >= restaurant["close_hour"]:
            continue

        if future_hour < restaurant["open_hour"]:
            continue

        if future_hour < 24:

            if not has_capacity(
                restaurant,
                day,
                future_hour
            ):
                continue

        available.append(option)

    return available


def option_names_to_indices(option_names):

    return np.array([
        OPTION_NAMES.index(name)
        for name in option_names
    ])


# ============================================================
# ACCEPTANCE MODEL
# ============================================================

def compute_acceptance_probability(customer, option_name):

    arm = ALL_OPTIONS[option_name]

    normalized_shift = (
        arm["time_shift"]
        / CONFIG["TIME_SHIFT_NORMALIZER"]
    )

    utility = CONFIG["BASE_UTILITY"]

    utility += (
        customer["discount_affinity"]
        * arm["discount"]
        * CONFIG["DISCOUNT_WEIGHT"]
    )

    utility += (
        (1 - customer["time_flexibility"])
        * (-normalized_shift)
        * CONFIG["TIME_SHIFT_WEIGHT"]
    )

    utility += (
        customer["urgency"]
        * (-normalized_shift)
        * CONFIG["URGENCY_DELAY_WEIGHT"]
    )

    utility += (
        customer["perk_affinity"]
        * arm["perk_value"]
        * CONFIG["PERK_WEIGHT"]
    )

    utility += (
        customer["restaurant_loyalty"]
        * CONFIG["LOYALTY_WEIGHT"]
    )

    if customer["requested_hour"] >= 19:

        utility -= (
            normalized_shift
            * CONFIG["EVENING_DELAY_PENALTY"]
        )

    if customer["group_size"] >= 5:

        utility -= (
            normalized_shift
            * CONFIG["GROUP_DELAY_PENALTY"]
        )

    utility += np.random.normal(
        0,
        CONFIG["NOISE_STD"]
    )

    probability = 1 / (1 + np.exp(-utility))

    return np.clip(
        probability,
        CONFIG["MIN_ACCEPTANCE_PROBABILITY"],
        CONFIG["MAX_ACCEPTANCE_PROBABILITY"]
    )


# ============================================================
# ENVIRONMENT
# ============================================================

class ReservationEnvironment:

    def __init__(self, customers):

        self.customers = customers
        self.t = 0

    def reset(self):
        self.t = 0

    def get_customer(self):
        return self.customers[self.t]

    def customer_choice(self, displayed_arm_indices):

        customer = self.get_customer()

        if len(displayed_arm_indices) == 0:
            return None, 0

        for arm_index in displayed_arm_indices:

            option_name = OPTION_NAMES[arm_index]

            p_accept = compute_acceptance_probability(
                customer,
                option_name
            )

            accepted = np.random.rand() < p_accept

            if accepted:
                return arm_index, 1

        return None, 0

    def step(self, displayed_arm_indices):

        chosen_arm, reward = self.customer_choice(
            displayed_arm_indices
        )

        self.t += 1

        done = self.t >= len(self.customers)

        return {
            "chosen_arm": chosen_arm,
            "reward": reward,
            "done": done
        }


# ============================================================
# BASE AGENT
# ============================================================

class BaseAgent:

    def __init__(self, n_arms):

        self.counts = np.zeros(n_arms)

        self.values = (
            np.ones(n_arms)
            * CONFIG["INITIAL_ACCEPTANCE_ESTIMATE"]
        )

    def update(self, arm, reward):

        self.counts[arm] += 1

        n = self.counts[arm]

        self.values[arm] += (
            reward - self.values[arm]
        ) / n


# ============================================================
# RANDOM
# ============================================================

class RandomAgent(BaseAgent):

    def select_arms(self, available_indices, k):

        return np.random.choice(
            available_indices,
            size=min(k, len(available_indices)),
            replace=False
        )


# ============================================================
# EPSILON GREEDY
# ============================================================

class EpsilonGreedyAgent(BaseAgent):

    def __init__(self, n_arms, epsilon=0.1):

        super().__init__(n_arms)

        self.epsilon = epsilon

    def select_arms(self, available_indices, k):

        if np.random.rand() < self.epsilon:

            return np.random.choice(
                available_indices,
                size=min(k, len(available_indices)),
                replace=False
            )

        available_scores = self.values[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1]


# ============================================================
# DECAY EPSILON
# ============================================================

class DecayEpsilonAgent(BaseAgent):

    def __init__(
        self,
        n_arms,
        epsilon_0=1.0,
        min_epsilon=0.01
    ):

        super().__init__(n_arms)

        self.epsilon_0 = epsilon_0
        self.min_epsilon = min_epsilon

        self.t = 1

    def select_arms(self, available_indices, k):

        epsilon = max(
            self.min_epsilon,
            self.epsilon_0 / np.sqrt(self.t)
        )

        self.t += 1

        if np.random.rand() < epsilon:

            return np.random.choice(
                available_indices,
                size=min(k, len(available_indices)),
                replace=False
            )

        available_scores = self.values[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1]


# ============================================================
# UCB1
# ============================================================

class UCB1Agent(BaseAgent):

    def __init__(self, n_arms, c=1):

        super().__init__(n_arms)

        self.c = c

        self.t = 1

    def select_arms(self, available_indices, k):

        available_indices = np.array(available_indices)

        unexplored = np.array([
            arm for arm in available_indices
            if self.counts[arm] == 0
        ])

        chosen = []

        if len(unexplored) > 0:

            chosen.extend(
                list(unexplored[:k])
            )

        remaining_needed = k - len(chosen)

        if remaining_needed > 0:

            remaining = np.array([
                arm for arm in available_indices
                if arm not in chosen
            ])

            if len(remaining) > 0:

                ucb_scores = self.values.copy()

                explored = self.counts > 0

                ucb_scores[explored] += (
                    self.c
                    * np.sqrt(
                        np.log(max(self.t, 2))
                        / self.counts[explored]
                    )
                )

                remaining_scores = ucb_scores[remaining]

                best_local = np.argsort(
                    remaining_scores
                )[-remaining_needed:]

                chosen.extend(
                    list(remaining[best_local])
                )

        self.t += 1

        return np.array(chosen)


# ============================================================
# THOMPSON SAMPLING
# ============================================================

class ThompsonSamplingAgent:

    def __init__(self, n_arms):

        self.alpha = np.ones(n_arms)

        self.beta = np.ones(n_arms)

    def select_arms(self, available_indices, k):

        samples = np.random.beta(
            self.alpha,
            self.beta
        )

        available_scores = samples[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1]

    def update(self, arm, reward):

        self.alpha[arm] += reward

        self.beta[arm] += 1 - reward


# ============================================================
# SOFTMAX
# ============================================================

class SoftmaxAgent(BaseAgent):

    def __init__(self, n_arms, temperature=0.1):

        super().__init__(n_arms)

        self.temperature = temperature

    def select_arms(self, available_indices, k):

        available_scores = self.values[available_indices]

        stable_scores = (
            available_scores
            - available_scores.max()
        )

        exp_scores = np.exp(
            stable_scores / self.temperature
        )

        probs = exp_scores / exp_scores.sum()

        return np.random.choice(
            available_indices,
            size=min(k, len(available_indices)),
            replace=False,
            p=probs
        )


# ============================================================
# AGENT REGISTRY
# ============================================================

AGENTS = {

    "Random": RandomAgent,

    "EpsilonGreedy": EpsilonGreedyAgent,

    "DecayEpsilon": DecayEpsilonAgent,

    "UCB1": UCB1Agent,

    "Thompson": ThompsonSamplingAgent,

    "Softmax": SoftmaxAgent
}


# ============================================================
# EXPERIMENT
# ============================================================

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


# ============================================================
# RUN EXPERIMENTS
# ============================================================

def main():

    all_results = []

    for k in CONFIG["N_SHOWN_OPTIONS_LIST"]:

        print("\n" + "=" * 60)
        print(f"TOP-K = {k}")
        print("=" * 60)

        topk_rows = []

        for agent_name, agent_class in AGENTS.items():

            run_rewards = []

            for run in range(CONFIG["N_RUNS"]):

                mean_reward = run_experiment(
                    agent_class,
                    k
                )

                run_rewards.append(mean_reward)

            mean_reward = np.mean(run_rewards)

            std_reward = np.std(run_rewards)

            ci95 = (
                1.96
                * std_reward
                / np.sqrt(CONFIG["N_RUNS"])
            )

            row = {

                "agent": agent_name,

                "top_k": k,

                "mean_reward": mean_reward,

                "std_reward": std_reward,

                "ci95": ci95,

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

            improvement = (
                (
                    row["mean_reward"]
                    - random_reward
                )
                / random_reward
            ) * 100

            row["improvement_vs_random_pct"] = improvement

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
                f"CI95=±{row['ci95']:.4f} | "
                f"improvement={row['improvement_vs_random_pct']:+.2f}%"
            )

    results_df = pd.DataFrame(all_results)

    results_df = results_df[[
        "top_k",
        "rank",
        "agent",
        "mean_reward",
        "std_reward",
        "ci95",
        "min_reward",
        "max_reward",
        "improvement_vs_random_pct"
    ]]

    print("\nFINAL RESULTS:")
    print(results_df.to_string(index=False))


    # ============================================================
    # PLOT
    # ============================================================

    plt.figure(figsize=(10, 6))

    for agent_name in results_df["agent"].unique():

        subset = results_df[
            results_df["agent"] == agent_name
        ]

        plt.plot(
            subset["top_k"],
            subset["mean_reward"],
            marker="o",
            label=agent_name
        )

    plt.xlabel("Number of shown alternatives (TOP-K)")
    plt.ylabel("Mean acceptance reward")
    plt.title("Bandit Strategy Comparison")
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
