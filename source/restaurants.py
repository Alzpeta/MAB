from .config import CONFIG
import numpy as np

RESTAURANT_CONFIGS = {

    0: {
        "name": "Lacny Tanier",
        "tier": "budget",
        "tag": "high-compensation",  # information-only tag
        "allowed_options": [
            "discount_20pct",
            "60min_plus_20pct",
            "60min_plus_15pct_plus_drink",
            "120min_plus_dessert",
            "free_drink",
            "180min_plus_apetizer",
            "180min_plus_15pct",
        ]
    },

    1: {
        "name": "U Hladneho Vlka",
        "tier": "budget",
        "tag": "low-compensation",
        "allowed_options": [
            "same_day_120min",
            "180min_plus_drink",
            "next_day_same_time",
            "discount_5pct",
            "priority_future_booking",
            "180min_plus_05pct_plus_dessert",
            "60min_plus_drink",
        ]
    },

    2: {
        "name": "Treska & Sen",
        "tier": "budget",
        "tag": "moderate",
        "allowed_options": [
            "discount_15pct",
            "priority_future_booking",
            "60min_plus_10pct",
            "120min_plus_10pct_plus_drink",
            "free_dessert",
            "next_day_plus_10pct",
            "60min_plus_drink",
        ]
    },

    3: {
        "name": "Kapustovy Dom",
        "tier": "budget",
        "tag": "high-compensation",
        "allowed_options": [
            "discount_20pct",
            "same_day_60min",
            "180min_plus_15pct",
            "120min_plus_15pct",
            "free_appetizer",
            "next_day_plus_10pct_plus_drink",
            "120min_plus_dessert",
        ]
    },
    4: {
        "name": "Rychla Bryndza",
        "tier": "budget",
        "tag": "low-compensation",
        "allowed_options": [
            "same_day_60min",
            "180min_plus_15pct",
            "180min_plus_apetizer",
            "discount_10pct",
            "priority_future_booking",
            "next_day_same_time",
            "same_day_120min",
        ]
    },

    5: {
        "name": "Zlaty Rezen",
        "tier": "midrange",
        "tag": "high-compensation",
        "allowed_options": [
            "discount_15pct",
            "180min_plus_20pct_plus_drink",
            "120min_plus_10pct_plus_drink",
            "120min_plus_vip",
            "free_dessert",
            "same_day_60min",
            "next_day_plus_vip",
        ]
    },

    6: {
        "name": "Knedla u Deda",
        "tier": "midrange",
        "tag": "moderate",
        "allowed_options": [
            "discount_10pct",
            "same_day_180min",
            "120min_plus_15pct",
            "60min_plus_drink",
            "vip_table_upgrade",
            "next_day_plus_vip",
            "120min_plus_10pct_plus_drink",
        ]
    },

    7: {
        "name": "Pirohove Nebo",
        "tier": "midrange",
        "tag": "low-compensation",
        "allowed_options": [
            "same_day_60min",
            "180min_plus_drink",
            "next_day_same_time",
            "discount_5pct",
            "120min_plus_dessert",
            "priority_future_booking",
            "120min_plus_5pct",
        ]
    },

    8: {
        "name": "Haluska Palace",
        "tier": "midrange",
        "tag": "moderate",
        "allowed_options": [
            "discount_10pct",
            "60min_plus_10pct_plus_drink",
            "120min_plus_5pct_plus_vip",
            "vip_table_upgrade",
            "same_day_180min",
            "next_day_plus_vip",
            "free_appetizer",
        ]
    },

    9: {
        "name": "Mastny Obrus",
        "tier": "midrange",
        "tag": "moderate",
        "allowed_options": [
            "discount_15pct",
            "same_day_60min",
            "180min_plus_20pct",
            "free_appetizer",
            "120min_plus_10pct_plus_drink",
            "next_day_plus_10pct",
            "120min_plus_dessert",
        ]
    },

    10: {
        "name": "Pan Hranolka",
        "tier": "premium",
        "tag": "low-compensation",
        "allowed_options": [
            "discount_5pct",
            "same_day_60min",
            "priority_future_booking",
            "vip_table_upgrade",
            "next_day_same_time",
            "180min_plus_drink",
            "120min_plus_dessert",
        ]
    },

    11: {
        "name": "Grand Bryndza",
        "tier": "premium",
        "tag": "high-compensation",
        "allowed_options": [
            "discount_10pct",
            "60min_plus_15pct_plus_drink",
            "120min_plus_vip",
            "vip_table_upgrade",
            "same_day_180min",
            "next_day_plus_vip",
            "120min_plus_10pct",
        ]
    },

    12: {
        "name": "Luxusny Gulas",
        "tier": "premium",
        "tag": "moderate",
        "allowed_options": [
            "discount_10pct",
            "same_day_120min",
            "priority_future_booking",
            "180min_plus_10pct_plus_vip",
            "free_appetizer",
            "next_day_plus_10pct",
            "60min_plus_10pct",
        ]
    },

    13: {
        "name": "Baron Parok",
        "tier": "premium",
        "tag": "low-compensation",
        "allowed_options": [
            "same_day_120min",
            "next_day_same_time",
            "discount_5pct",
            "priority_future_booking",
            "180min_plus_05pct_plus_dessert",
            "vip_table_upgrade",
            "180min_plus_drink",
        ]
    },

    14: {
        "name": "Kralovsky Langoš",
        "tier": "premium",
        "tag": "high-compensation",
        "allowed_options": [
            "discount_10pct",
            "60min_plus_20pct",
            "120min_plus_20pct",
            "120min_plus_5pct_plus_vip",
            "vip_table_upgrade",
            "next_day_plus_20pct",
            "60min_plus_15pct_plus_drink",
        ]
    },
}


def generate_restaurants(restaurant_tiers=None):
    restaurants = []

    restaurant_tiers = (
        set(restaurant_tiers)
        if restaurant_tiers is not None
        else None
    )

    restaurant_items = [
        (
            restaurant_id,
            RESTAURANT_CONFIGS[restaurant_id]
        )
        for restaurant_id in range(len(RESTAURANT_CONFIGS))
    ]

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
                    1.00
                )

                occupied = int(
                    occupancy_ratio
                    * CONFIG["SLOTS_PER_HOUR"]
                )

                calendar[day][hour] = occupied

        calendar[CONFIG["N_DAYS"]] = calendar[0]

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
