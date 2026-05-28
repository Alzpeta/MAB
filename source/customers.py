from .config import CONFIG
import numpy as np

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

            "group_size": np.random.choice(
                [1, 2, 3, 4, 5, 6, 7],
                p=[0.15, 0.35, 0.2, 0.12, 0.1, 0.05, 0.03]
            )

        }

        customers.append(customer)

    return customers