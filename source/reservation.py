from .config import CONFIG
from .options import ALL_OPTIONS, OPTION_NAMES
import numpy as np

def has_capacity(restaurant, day, hour, group_size):

    return (
        restaurant["calendar"][day][hour] + group_size
        <= CONFIG["SLOTS_PER_HOUR"]
    )


def get_available_options(customer):

    restaurant = customer["restaurant"]

    day = customer["requested_day"]
    hour = customer["requested_hour"]
    group_size = customer["group_size"]

    available = []

    for option in restaurant["allowed_options"]:

        arm = ALL_OPTIONS[option]
        time_shift = int(np.ceil(arm["time_shift"] / 60))

        if time_shift == 24:

            if not has_capacity(
                    restaurant,
                    day + 1,
                    hour,
                    group_size
                ):
                    continue
        elif time_shift > 0:

            future_hour = hour + time_shift

            if future_hour >= restaurant["close_hour"]:
                continue

            elif not has_capacity(
                restaurant,
                day,
                future_hour,
                group_size
            ):
                continue

        available.append(option)

    return available


def option_names_to_indices(option_names):

    return np.array([
        OPTION_NAMES.index(name)
        for name in option_names
    ])

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

    utility -= (
        arm["requires_future_visit"]
        * customer["future_visit_frustration"]
        * CONFIG["FUTURE_VISIT_FRUSTRATION_WEIGHT"] #default as 1
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
