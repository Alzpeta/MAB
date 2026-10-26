from .config import CONFIG
import numpy as np

def generate_customers(restaurants, rng=None):

    rng = np.random if rng is None else rng

    customers = []

    for customer_id in range(CONFIG["N_CUSTOMERS"]):

        restaurant = rng.choice(restaurants)

        day_weights = np.ones(CONFIG["N_DAYS"])
        day_weights[CONFIG["WEEKEND_DAYS"]] += CONFIG["WEEKEND_OCCUPANCY_BOOST"]
        day_probabilities = day_weights / day_weights.sum()

        hours = np.arange(CONFIG["OPEN_HOUR"], CONFIG["CLOSE_HOUR"])
        hour_weights = np.ones(len(hours))
        hour_weights[np.isin(hours, CONFIG["EVENING_PEAK_HOURS"])] += CONFIG["EVENING_OCCUPANCY_BOOST"]
        hour_probabilities = hour_weights / hour_weights.sum()

        customer = {

            "customer_id": customer_id,

            "restaurant": restaurant,

            "restaurant_id": restaurant["restaurant_id"],

            "requested_day":
                rng.choice(
                    np.arange(CONFIG["N_DAYS"]),
                    p=day_probabilities
                ),

            "requested_hour":
                rng.choice(
                    hours,
                    p=hour_probabilities
                ),

            "discount_affinity":
                np.clip(
                    rng.normal(
                        CONFIG["DISCOUNT_AFFINITY_MEAN"],
                        CONFIG["DISCOUNT_AFFINITY_STD"]
                    ),
                    0,
                    1
                ),

            "time_flexibility":
                np.clip(
                    rng.normal(
                        CONFIG["TIME_FLEXIBILITY_MEAN"],
                        CONFIG["TIME_FLEXIBILITY_STD"]
                    ),
                    0,
                    1
                ),

            "restaurant_loyalty":
                np.clip(
                    rng.normal(
                        CONFIG["LOYALTY_MEAN"],
                        CONFIG["LOYALTY_STD"]
                    ),
                    0,
                    1
                ),

            "perk_affinity":
                np.clip(
                    rng.normal(
                        CONFIG["PERK_AFFINITY_MEAN"],
                        CONFIG["PERK_AFFINITY_STD"]
                    ),
                    0,
                    1
                ),

            "urgency":
                np.clip(
                    rng.normal(
                        CONFIG["URGENCY_MEAN"],
                        CONFIG["URGENCY_STD"]
                    ),
                    0,
                    1
                ),

            "group_size": rng.choice(
                [1, 2, 3, 4, 5, 6, 7],
                p=[0.15, 0.35, 0.2, 0.12, 0.1, 0.05, 0.03]
            )

        }

        customer["future_visit_frustration"] = (
            0.5 * customer["urgency"]
            + 0.5 * (1 - customer["time_flexibility"])
        )

        customers.append(customer)

    return customers
