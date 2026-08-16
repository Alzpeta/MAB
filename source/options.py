ALL_OPTIONS = {

    # pure time shift
    "same_day_60min": {
        "time_shift": 60,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_120min": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_180min": {
        "time_shift": 180,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    # next day offer
    "next_day_same_time": {
        "time_shift": 1440,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "next_day_plus_10pct": {
        "time_shift": 1440,
        "requires_future_visit": 0,
        "discount": 0.10,
        "perk_value": 0.00,
    },

    "next_day_plus_vip": {
        "time_shift": 1440,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.35,
    },

    "next_day_plus_20pct": {
        "time_shift": 1440,
        "requires_future_visit": 0,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    "next_day_plus_drink": {
        "time_shift": 1440,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.18,
    },

    # pure discount
    "discount_5pct": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.05,
        "perk_value": 0.00,
    },

    "discount_10pct": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.10,
        "perk_value": 0.00,
    },

    "discount_15pct": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.15,
        "perk_value": 0.00,
    },

    "discount_20pct": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    # pure perks
    "free_drink": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.00,
        "perk_value": 0.18,
    },
    "free_appetizer": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.00,
        "perk_value": 0.28,
    },
    "free_dessert": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.00,
        "perk_value": 0.24,
    },
    "vip_table_upgrade": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.00,
        "perk_value": 0.34,
    },

    "priority_future_booking": {
        "time_shift": 0,
        "requires_future_visit": 1,
        "discount": 0.00,
        "perk_value": 0.22,
    },

    # delay + discount
    "60min_plus_5pct": {
        "time_shift": 60,
        "requires_future_visit": 0,
        "discount": 0.05,
        "perk_value": 0.00,
    },

    "60min_plus_10pct": {
        "time_shift": 60,
        "requires_future_visit": 0,
        "discount": 0.10,
        "perk_value": 0.00,
    },

    "120min_plus_10pct": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.10,
        "perk_value": 0.00,
    },
    "120min_plus_15pct": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.15,
        "perk_value": 0.00,
    },
    "180min_plus_15pct": {
        "time_shift": 180,
        "requires_future_visit": 0,
        "discount": 0.15,
        "perk_value": 0.00,
    },
    "180min_plus_20pct": {
        "time_shift": 180,
        "requires_future_visit": 0,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    # delay + perk
    "60min_plus_drink": {
        "time_shift": 60,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.18,
    },
    "120min_plus_dessert": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.24,
    },

    "120min_plus_vip": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.34,
    },

    "180min_plus_apetizer": {
        "time_shift": 180,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.28,
    },

    # mixed

    "60min_plus_10pct_plus_drink": {
        "time_shift": 60,
        "requires_future_visit": 0,
        "discount": 0.10,
        "perk_value": 0.18,
    },

    "60min_plus_5pct_plus_dessert": {
        "time_shift": 60,
        "requires_future_visit": 0,
        "discount": 0.05,
        "perk_value": 0.24,
    },

    "180min_plus_10pct_plus_vip": {
        "time_shift": 180,
        "requires_future_visit": 0,
        "discount": 0.10,
        "perk_value": 0.34,
    },

    "120min_plus_10pct_plus_drink": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.10,
        "perk_value": 0.18,
    },

    "180min_plus_05pct_plus_dessert": {
        "time_shift": 180,
        "requires_future_visit": 0,
        "discount": 0.05,
        "perk_value": 0.24,
    },

    # nelinarni options
    "60min_plus_20pct": {
        "time_shift": 60,
        "requires_future_visit": 0,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    "180min_plus_drink": {
        "time_shift": 180,
        "requires_future_visit": 0,
        "discount": 0.00,
        "perk_value": 0.18,
    },

    "120min_plus_20pct": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    "60min_plus_15pct_plus_drink": {
        "time_shift": 60,
        "requires_future_visit": 0,
        "discount": 0.15,
        "perk_value": 0.18,
    },

    "120min_plus_5pct_plus_vip": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.05,
        "perk_value": 0.34,
    },
    "120min_plus_5pct": {
        "time_shift": 120,
        "requires_future_visit": 0,
        "discount": 0.05,
        "perk_value": 0.00,
    },

    "180min_plus_20pct_plus_drink": {
        "time_shift": 180,
        "requires_future_visit": 0,
        "discount": 0.20,
        "perk_value": 0.18,
    },

    "next_day_plus_10pct_plus_drink": {
        "time_shift": 1440,
        "requires_future_visit": 0,
        "discount": 0.10,
        "perk_value": 0.18,
    },
}

def option_category(option_name):

    option = ALL_OPTIONS[option_name]
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

OPTION_NAMES = list(ALL_OPTIONS.keys())

N_ARMS = len(OPTION_NAMES)
