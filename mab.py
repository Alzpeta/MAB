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
"""
   jeden run = vygeneruje se cely environment, probehne vsech 20 000 customers, agent se postupne uci
   v kazdem runu se znova vygeneruji novy customers, tzn maji jine vlastnosti
   je jina occupancy
   jiny behavioral noise
   ty agenti maji jine chovani
   tzn jeden run muzou byt ti customers ze berou vsechno, jednou ze nic a ve vysledkyu je prumer
   
   "EVENING_OCCUPANCY_BOOST": 0.35, o kolik se vecer zvysi obsazenost restaurace
pouziva se jen pri generovani?
   """

CONFIG = {

    # ========================================================
    # EXPERIMENT
    # ========================================================

    "N_CUSTOMERS": 20000,

    "N_RUNS": 30, # pocet behu pro kazdou strategii - pak se udela prumer

    "SEED": 33,

    "N_SHOWN_OPTIONS_LIST": [1,2,3,5],

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

    "EVENING_OCCUPANCY_BOOST": 0.20, #uprava z 0.35 jinak bylo skoro vzdy vecer full u premium

    "WEEKEND_DAYS": [4, 5], #patek, sobota, indexujeme od 0

    "WEEKEND_OCCUPANCY_BOOST": 0.15, #uprava z 0.20 na 0,1 jinak o vikendu furt full

    "TIER_BASE_OCCUPANCY": {
            # "budget": 1.0,
            # "midrange": 1.0,
            # "premium": 1.0,
        "budget": 0.45,
        "midrange": 0.60,
        "premium": 0.75,
    },

    # ========================================================
    # BANDIT SETTINGS
    # ========================================================

    "INITIAL_ACCEPTANCE_ESTIMATE": 0.15, #pocatecni odhad rewardu pro kazdy arm

    #kdyz dame treba 50, bude to strasne optimisticky a bude dlouho explorovat, protoze ocekava vysoke rewardy
    # 0,1 zase bude prilis brzo exploitovat
    #tohle by nemelo moc ovlivnovat thompson
    # ========================================================
    # CUSTOMER DISTRIBUTIONS
    # ========================================================

    #np.random.normal(mean, std) tady pak pouzity, generujeme to dle nahodneho rozdeleni

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

    #aka jak customer dela ta rozhodnuti

    "BASE_UTILITY": -2.0, #aka vychozi nalada, customer nechce defaultne prijmout alternativu
    #je nastvany, protoze nema rezervaci, takze jde do toho s negativni naladou a musime ho presvedcovat
    #-5 uz by nas poslal nekam, 0 bude spis vse prijimat

    #tohle je zalozeno na utility based choice modeling
    #clovek ma nejakou utility podle ktere se rozhoduje, je to klasicky v ekonometrii, behavioral modelingu atp
    # U=β0+β1x1+β2x2+...
    # x jsou vahy, b jsou preferencni features
    #logistic mapping je zas pak klasicky vzorec co se pouziva kde se to pouzije
    # k tomu utility se pak pridav noise, protoze lidske chovani neni perfektne deterministicke
    # random utility theory.

    #tohle dal jsou parametry naseho syntetickeho sveta
    #nekteri lidi miluji slevy, nekdo specha, nekdo je flexibilni, nekdo ma radsi bonus nez slevu,
    #loayalni customers snesou vic
    #"custom utility-based synthetic user simulator"
    "DISCOUNT_WEIGHT": 3.0, #jak moc zakaznici ocenuji slevu

    "TIME_SHIFT_WEIGHT": 2.5, #jak moc lidem vadi delay

    "PERK_WEIGHT": 1.0, #jak moc funguji bonusy (perky) [free piti atp]
        #tzn min to funguje jak discount
    "LOYALTY_WEIGHT": 0.1, #maly bonus za loyal customer behavior, pokud ma customer rad restiku, bude trosicku tolerantnejsi


    "URGENCY_DELAY_WEIGHT": 2.0, #urgency delay - tem co jsou urgent bude cekani mega vadit


    "EVENING_DELAY_PENALTY": 0.7, # ti co si to zarezervuji vecer budou min flexibilni, rpotoze vic vazane socialne atp

    "GROUP_DELAY_PENALTY": 0.7, # velke skupiny hur toleruji delay

    "NOISE_STD": 0.6, # mira nepredvidatelnosti lidskeho chovani

    # ========================================================
    # NORMALIZATION
    # ========================================================

    "TIME_SHIFT_NORMALIZER": 1440, #normalizace timeshiftu- je to na 24 hod == 1440 minut

    # ========================================================
    # ACCEPTANCE PROBABILITY CLIPPING
    # ========================================================

    #ochrana proti extremum
    #kdyz probability vyjde jako 0,0000001, clipne se to na 0,01
    # kdyz 0.9999999 tak na 0.95
    #jinak by nektere offers byly temer vzdy akceptoatelen a nektere nikdy
    #tzn skoro deterministicke situace
    #pak by to bylo pro banditu moc easy
    #kdyby to davalo 0,999 tak by po tom sel vzdy
    #zadna nabidka neni uplne stopro success a zaroven zadna neni impossible
    "MIN_ACCEPTANCE_PROBABILITY": 0.01,
    "MAX_ACCEPTANCE_PROBABILITY": 0.95,
}

np.random.seed(CONFIG["SEED"]) #todo whyyy


# ============================================================
# OPTION CATALOG
# ============================================================

#menim timeshift na cele hours, protoze zbytek kodu je nastaveny na cele hours a nedava to dal smysl
#samotny options muzou byt matematicky lepsi, ale nesmi byt akto ve stejne restauraci!!!!
#TODO:checknout to
ALL_OPTIONS = {

    # -------------------------
    # PURE TIME SHIFTS
    # -------------------------

    "same_day_60min": {
        "time_shift": 60,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_120min": {
        "time_shift": 120,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "same_day_180min": {
        "time_shift": 180,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    # -------------------------
    # NEXT DAY OFFERS
    # -------------------------
    "next_day_same_time": {
        "time_shift": 1440,
        "discount": 0.00,
        "perk_value": 0.00,
    },

    "next_day_plus_10pct": {
        "time_shift": 1440,
        "discount": 0.10,
        "perk_value": 0.00,
    },

    "next_day_plus_vip": {
        "time_shift": 1440,
        "discount": 0.00,
        "perk_value": 0.35,
    },

    "next_day_plus_20pct": {
        "time_shift": 1440,
        "discount": 0.20,
        "perk_value": 0.00,
    },
    # -------------------------
    # PURE DISCOUNTS
    # IMPORTANT:
    # only one pure discount
    # should exist per restaurant
    # -------------------------
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

    # -------------------------
    # PURE PERKS
    # intentionally NOT ordered
    # linearly to avoid dominance
    # -------------------------
    "free_drink": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.18,
    },
    "free_appetizer": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.28,
        },
    "free_dessert": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.24,
    },

    "vip_table_upgrade": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.34,
    },

    "priority_future_booking": {
        "time_shift": 0,
        "discount": 0.00,
        "perk_value": 0.22,
    },

    # -------------------------
    # DELAY + DISCOUNT
    # -------------------------

    "60min_plus_5pct": {
        "time_shift": 60,
        "discount": 0.05,
        "perk_value": 0.00,
    },

    "60min_plus_10pct": {
        "time_shift": 60,
        "discount": 0.10,
        "perk_value": 0.00,
    },

    "120min_plus_10pct": {
        "time_shift": 120,
        "discount": 0.10,
        "perk_value": 0.00,
    },
    "120min_plus_15pct": {
        "time_shift": 120,
        "discount": 0.15,
        "perk_value": 0.00,
    },
    "180min_plus_15pct": {
        "time_shift": 180,
        "discount": 0.15,
        "perk_value": 0.00,
    },
    "180min_plus_20pct": {
        "time_shift": 180,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    # -------------------------
    # DELAY + PERK
    # -------------------------

    "60min_plus_drink": {
        "time_shift": 60,
        "discount": 0.00,
        "perk_value": 0.18,
    },
    "120min_plus_dessert": {
        "time_shift": 60,
        "discount": 0.00,
        "perk_value": 0.24,
    },

    "120min_plus_vip": {
        "time_shift": 60,
        "discount": 0.00,
        "perk_value": 0.34,
    },

    "180min_plus_apetizer": {
        "time_shift": 120,
        "discount": 0.00,
        "perk_value": 0.28,
    },

    # -------------------------
    # MIXED TRADEOFFS
    # -------------------------

    "60min_plus_10pct_plus_drink": {
        "time_shift": 60,
        "discount": 0.10,
        "perk_value": 0.18,
    },

    "60min_plus_5pct_plus_dessert": {
        "time_shift": 60,
        "discount": 0.05,
        "perk_value": 0.24,
    },

    "180min_plus_10pct_plus_vip": {
        "time_shift": 180,
        "discount": 0.10,
        "perk_value": 0.34,
    },

    "120min_plus_10pct_plus_drink": {
        "time_shift": 120,
        "discount": 0.10,
        "perk_value": 0.18,
    },

    "180min_plus_05pct_plus_dessert": {
        "time_shift": 180,
        "discount": 0.05,
        "perk_value": 0.24,
    },

    #nelinarni options
    "60min_plus_20pct": { #mega vyhodne
        "time_shift": 60,
        "discount": 0.20,
        "perk_value": 0.00,
    },

    "180min_plus_drink": {
    "time_shift": 180,
    "discount": 0.00,
    "perk_value": 0.18,
    },

    "120min_plus_20pct": {
    "time_shift": 120,
    "discount": 0.20,
    "perk_value": 0.00,
    },

    "next_day_plus_drink": {
    "time_shift": 1440,
    "discount": 0.00,
    "perk_value": 0.18,
},

"60min_plus_15pct_plus_drink": {
    "time_shift": 60,
    "discount": 0.15,
    "perk_value": 0.18,
},

"120min_plus_5pct_plus_vip": {
    "time_shift": 120,
    "discount": 0.05,
    "perk_value": 0.34,
},
"120min_plus_5pct": {
    "time_shift": 120,
    "discount": 0.05,
    "perk_value": 0.00,
},

"180min_plus_20pct_plus_drink": {
    "time_shift": 180,
    "discount": 0.20,
    "perk_value": 0.18,
},

"next_day_plus_10pct_plus_drink": {
    "time_shift": 1440,
    "discount": 0.10,
    "perk_value": 0.18,
},
}

OPTION_NAMES = list(ALL_OPTIONS.keys())

N_ARMS = len(OPTION_NAMES)


# ============================================================
# RESTAURANTS
# ============================================================

#todo: checknout to + jestli tam jsou options co se nepouzily + jestli nejaka restaurace neni uplne stejna + mozna dat options kategorie a podle nich to tez hodnotit
RESTAURANT_CONFIGS = {

    0: {
        "name": "Lacny Tanier",
        "tier": "budget",
        # velmi hodna restaurace
        "allowed_options": [
            "discount_20pct",
            "60min_plus_20pct",
            "60min_plus_15pct_plus_drink",
            "120min_plus_dessert",
            "free_drink",
            "same_day_60min",
            "next_day_plus_10pct",
        ]
    },

    1: {
        "name": "U Hladneho Vlka",
        "tier": "budget",
        # spis zla restaurace
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
        # normal balanced
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
        # trochu hodna
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
        # trochu zla
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
        # hodna
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
        # neutral
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
        # zla
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
        # premium wannabe
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
         # chaotic balanced
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
         # arrogant premium
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
        # hodna premium
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
        # balanced premium
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
        # evil luxury place
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
        # overcompensating fancy place
        "allowed_options": [
            "discount_15pct",
            "60min_plus_20pct",
            "120min_plus_20pct",
            "120min_plus_5pct_plus_vip",
            "vip_table_upgrade",
            "next_day_plus_20pct",
            "60min_plus_15pct_plus_drink",
        ]
    },
}


# ============================================================
# RESTAURANTS
# ============================================================

def generate_restaurants(restaurant_tiers=None): #pokud none, vytvorime vsechny, pokud tier, vytvorime jen ty z tieru

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
                for restaurant_id in range(CONFIG["N_RESTAURANTS"])
            ]
    #restaurant item: [(0, {'allowed_options': ['xy', 'yx'], 'name' ...}), ..]
    for restaurant_id, config in restaurant_items:

        if (
            restaurant_tiers is not None
            and config["tier"] not in restaurant_tiers
        ):
            continue

        #todo: ted je problem, ze mame jen 7 dnu a osoba muze prijit o 24 hodin pozdeji a checkujeme zda je misto - ten den neexistuje
        #fixed: udelam to tak, ze den 0 je tam 2x - tzn opakuju ten stejny tyden, dalsi pondeli je to stejne co to predchozi
        #todo: jsme s tim takto v poho?
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

                if hour in CONFIG["EVENING_PEAK_HOURS"]: #pokud jsem v peak hodine tak pricteme boost. zacali sme treba na 0.45 tzn +0.35

                    occupancy_ratio += (
                        CONFIG["EVENING_OCCUPANCY_BOOST"]
                    )

                if day in CONFIG["WEEKEND_DAYS"]:

                    occupancy_ratio += (
                        CONFIG["WEEKEND_OCCUPANCY_BOOST"] #+0.25 (tzn sme v peaku o vikendu na 1.05
                    )

                occupancy_ratio += np.random.normal(
                    0,
                    0.08
                ) #pridame tam random bordel, treba -0.02550828040865042, -0.1 atp atp, nebo +0.1
                # a my se treba v peaku dostaneme proste na 135 procent coz je bullshit, takze clip na max 100
                occupancy_ratio = np.clip(
                    occupancy_ratio,
                    0.05, #todo: nebo 0??
                    1.00
                )

                occupied = int(
                    occupancy_ratio
                    * CONFIG["SLOTS_PER_HOUR"]
                )

                calendar[day][hour] = occupied
        calendar[7] = calendar[0] #fix: osoba v nedeli uz muze dostat termin na dalsi den
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

        restaurant = np.random.choice(restaurants) #jde do random restiky
        #todo: ono ty premium mame vice obsazene, takze by mohlo byt ze do nich chodi vic lidi? ale spis to nechat takto

        customer = {

            "customer_id": customer_id,

            "restaurant": restaurant,

            "restaurant_id": restaurant["restaurant_id"], #duplicitni info

            "requested_day":
                np.random.randint(0, CONFIG["N_DAYS"]), #todo: taky, tvrdime, ze vecer chodi lidi vic, ale pak chodi uplne random

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

            "restaurant_loyalty": #vzdy loajalni k ty kam jdou, toto mi prijde fer, nedavala bych to ze jsou loajalni ke konkretni
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
            #do ted se nebralo v potaz pri reseni, jestli je plno
            #to ze jde skupina dvou lidi neni stejne pravdepodobne jako 7 imo
            "group_size": np.random.choice(
                [1, 2, 3, 4, 5, 6, 7],
                p=[0.15, 0.35, 0.2, 0.12, 0.1, 0.05, 0.03]
            )
            # "group_size":
            #     np.random.randint(1, 7)
        }

        customers.append(customer)

    return customers


# ============================================================
# AVAILABILITY
# ============================================================

def has_capacity(restaurant, day, hour, group_size):

    return (
        restaurant["calendar"][day][hour] + group_size #kolik tam je plus kolik jich jde musi byt mensi rovno kapacite
        <= CONFIG["SLOTS_PER_HOUR"]
    )


def get_available_options(customer):
    #takze to funguje tak, ze vlastne i kdyz je volno, tak jakoby neni, right?
    restaurant = customer["restaurant"]

    day = customer["requested_day"]
    hour = customer["requested_hour"]
    group_size = customer["group_size"]

    available = []
    #todo - udelat kalendar loop aby to vyresilo kdyz nekdo prijde v nedeli tak abychom nepretekli
    for option in restaurant["allowed_options"]:

        arm = ALL_OPTIONS[option]
        time_shift = int(np.ceil(arm["time_shift"] / 60))

        #dobry, takze ty options +45 atp jsou ted ve smes uplna hovadina v tuhle cast
        #protoze se to zaokrouhluje na cele hodiny
        # todo: co se stane, kdyz neni mozne mit dost available options?
        # coz se dost jasne stat muze zejo, kdyz jich nabizim 5 ale jen 3 muzu nabidnout
        if time_shift == 24: #ta osoba musi rezervovat oteviraci dobu tzn pristi den bude urco bezpecne v oteviraci dobe
            if not has_capacity(
                    restaurant,
                    day + 1,
                    hour,
                    group_size
                ):
                    continue
        else:

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


# ============================================================
# ACCEPTANCE MODEL
# ============================================================

def compute_acceptance_probability(customer, option_name):

    arm = ALL_OPTIONS[option_name]

    #time shift ma uplne jiny scale nez zbytek utilit, musi to byt od 0 do 1 jako zbytek, jinak to bude strasne bias
    #jinak by to proste vzdy bylo 0
    #todo: normalizovat nejak trochu jinak? za me takto cajk
    normalized_shift = (
        arm["time_shift"]
        / CONFIG["TIME_SHIFT_NORMALIZER"]
    )

    utility = CONFIG["BASE_UTILITY"] #vychozi ochota zakaznika to prijmout,

    #kdyz je tam discount tak se jeho nastaveni zvedne
    #tady muzeme jit jen do plusu
    utility += (
        customer["discount_affinity"]
        * arm["discount"]
        * CONFIG["DISCOUNT_WEIGHT"]
    )

    #flexibilita - jak moc zakaznikovi vadi posunuti rezervace
    #0 == vubec neni flexibilni, 1 = je mu to dost jedno
    utility += (
        (1 - customer["time_flexibility"]) #kdyz je mu to jedno, nic se neodecte
        * (-normalized_shift)
        * CONFIG["TIME_SHIFT_WEIGHT"]
    )
    #jako moc to popravde neodecita, ale zas je tam pak jeste ta urgence tak..

    #flexibility == personality trait, urgency == situation state
    #todo: lehce redundatni, za me ok
    #urgency 0 - je uplne v chillu a je mu to jedno urgency 1 - je to nejdulezitejsi akce jeho zivota
    utility += (
        customer["urgency"]
        * (-normalized_shift)
        * CONFIG["URGENCY_DELAY_WEIGHT"]
    )
    #jak moc se necha oblbnout vecma zadarmo atp, 0 vubec, 1 mega moc, ciste pozitivni vstup
    utility += (
        customer["perk_affinity"]
        * arm["perk_value"]
        * CONFIG["PERK_WEIGHT"]
    )
    #jak moc ma loajalitu k te restice
    utility += (
        customer["restaurant_loyalty"]
        * CONFIG["LOYALTY_WEIGHT"]
    )

    if customer["requested_hour"] >= 19: #vecer je min flexibilni

        utility -= (
            normalized_shift
            * CONFIG["EVENING_DELAY_PENALTY"]
        )

    if customer["group_size"] >= 5: #vic lidi to bude vic iritovat ze se to posouva

        utility -= (
            normalized_shift
            * CONFIG["GROUP_DELAY_PENALTY"]
        )
    #random cislo okolo 0, jak plus tak i minus
    utility += np.random.normal( #a nejaky random noise do toho vseho
        0,
        CONFIG["NOISE_STD"]
    )

    probability = 1 / (1 + np.exp(-utility)) #sigmoid funkce proste - prevedu na pravdepodobnost
    #todo, dava to nejak v pohode acceptance?
    #zase boj proti determinismu: (i uplne debilni nabidka ted muze cas od casu projit, neb takovy je zivot
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
        self.t = 0 #time step

    def reset(self):
        self.t = 0 #reset pred kazdym novym runem

    def get_customer(self):
        return self.customers[self.t] #kazdy customer je jeden step

    def customer_choice(self, displayed_arm_indices):

        customer = self.get_customer()
        #tady sme ve fazi ze teda prisli option
        if len(displayed_arm_indices) == 0: #hm co se realne teda stane kdyz nezobrazim nic nebo malo??
            return None, 0 #todo: takze vlastne banditovi rikame ze to nezvladl? je to cajk?
            #todo: neni lepsi skip??

        for arm_index in displayed_arm_indices:

            option_name = OPTION_NAMES[arm_index]

            p_accept = compute_acceptance_probability(
                customer,
                option_name
            )
            #hodim si kostkou a jestli je to min nez p accept tak to prijal
            accepted = np.random.rand() < p_accept

            if accepted: #prvni co vezmu
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

        self.counts = np.zeros(n_arms) #kolkrat byl dany arm vybrany, pokud 3 army, tak pole 3 0
        #mysleno, kolikrat ot ten agent navrhnul??
        self.values = ( #odhad prumerneho rewardu armu
            np.ones(n_arms)
            * CONFIG["INITIAL_ACCEPTANCE_ESTIMATE"]
        ) #jak dobry si myslim ze arm je
        #initial je proste to jak to mame nastavene array([0.15, 0.15, 0.15])

    def update(self, arm, reward): #ok sem se dostanu pokud to acceptne customer
        #todo: projit
        self.counts[arm] += 1

        n = self.counts[arm]

        self.values[arm] += (
            reward - self.values[arm]
        ) / n #prepocitam tu value, coz btw po 1 acceptu je ted od 0.15 na 0.85, to je dost ne?
        #early lucky/unlucky samples maji obri vliv
        #proto ted thompson dominuje, protoze ten toto tolik neresi, ale chudak ubt je v prcici
        #TODO: zkusit toto pozmenit no
        #menila bych to ale pres ten acceptance rate co je primo v cfg
# ============================================================
# RANDOM
# ============================================================

class RandomAgent(BaseAgent):

    def select_arms(self, available_indices, k):
        #k je kolik toho muzu vybrat, tzn random z toho vyberu vezmu k
        return np.random.choice(
            available_indices,
            size=min(k, len(available_indices)), #pokud min options nez muzu, tak vezmu tolik kolik toho je
            #kdyz 0 tak 0 - ono se to nestane nikdy ze by tam slo 0 realne, protoze kazda restaurace ma nejakou option co neni casove zavisla..
            replace=False #bez opakova, tzn nemuzu dvakrat selectnout stejny arm, tak se to historicky jmenuje proste, ze nevracim kulicku zpet do pytlicku na los..
        ) #todo: ale stejne, discuss


# ============================================================
# EPSILON GREEDY
# ============================================================

class EpsilonGreedyAgent(BaseAgent):

    def __init__(self, n_arms, epsilon=0.1):

        super().__init__(n_arms)

        self.epsilon = epsilon #epsilon == pravdepodobnost explorace
        #toto mimo testy realne nemenime, je to klasicky zvoleny cislo
    def select_arms(self, available_indices, k):

        if np.random.rand() < self.epsilon: #klasika, hazu kostkou od 0 do 1, pokud min jak 0,1, jdu explorovat
            #pak jdu uplne random
            return np.random.choice(
                available_indices,
                size=min(k, len(available_indices)),
                replace=False
            )
        #mne chodi indexy tech options a to odpovida indexu tech values.
        available_scores = self.values[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:] #vezmu k nejvetsich values

        return available_indices[best_local][::-1] #zas skutecne indexy tech arms


# ============================================================
# DECAY EPSILON
# ============================================================
#na zacatku hodne explorujeme a pak vic exploitujeme kdyz uz mame data
class DecayEpsilonAgent(BaseAgent):

    def __init__(
        self,
        n_arms,
        epsilon_0=1.0, #zaciname se stejnym epsilon, ale to postupne klesa
        min_epsilon=0.01 #az sem
    ):

        super().__init__(n_arms)

        self.epsilon_0 = epsilon_0
        self.min_epsilon = min_epsilon

        self.t = 1 #dela se to epsilon_0 / sqrt(t), pro 10 000 uz je to tech 0.01 takze pak jedeme na min
        #pro 1.0 je t =1

    def select_arms(self, available_indices, k):

        epsilon = max( #bud beru to prepocitane epsilon, nebo minimum
            self.min_epsilon,
            self.epsilon_0 / np.sqrt(self.t)
        )

        self.t += 1 #tady musim kvuli tomu jet vlastni t

        if np.random.rand() < epsilon: #the same

            return np.random.choice(
                available_indices,
                size=min(k, len(available_indices)),
                replace=False
            )
        #the sameeee - kdyby bylo potreba to menit, nejak to slit, ale jinak asi ok ze to neni uplne krasny kod
        available_scores = self.values[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1]


# ============================================================
# UCB1
# ============================================================
#upper confidence bound - chci vybirat co ma vysokou prumernou hodnotu ale cas od casu zkusit explore
class UCB1Agent(BaseAgent):

    #ucb pro arm je = prumerny reward armu + c krat sqrt logt / na
    #na je kolikrat byl arm vyzkousen
    #to jede pro vsechny ty arms
    #tzn vezme prumer co uz vim a pricte k tomu tzv exploracni bonus
    def __init__(self, n_arms, c=1):

        super().__init__(n_arms)

        self.c = c #to je proste cast vzorecku

        self.t = 1 #to je taky vec co potrebujeme ve vzorecku
        #todo, ty stretegie co jedou na t tak zalezi kolik mam customers, takze? zkusit to pak zvednout
        #technicky ale je realisticky ze rezervobot tolik lidi nebude pouzivat, nic ve zlem

    def select_arms(self, available_indices, k):

        available_indices = np.array(available_indices)
        #on musi kazdy arm alespon jednou videt, jina bych delila nulou - na by byl 0
        unexplored = np.array([ #najde army co jeste nezkusil, tzn maji 0
            arm for arm in available_indices
            if self.counts[arm] == 0
        ])

        chosen = []

        if len(unexplored) > 0:

            chosen.extend( #kdyz jeste nezkusil vic jak k tak vezme proste tyto a konci
                list(unexplored[:k])
            )

        remaining_needed = k - len(chosen) #kolik zbyva zejo aby se to veslo do k

        if remaining_needed > 0:

            remaining = np.array([ #proste ten zbytek co jeste neni v chosen - jejich indexy
                arm for arm in available_indices
                if arm not in chosen
            ])

            if len(remaining) > 0:

                ucb_scores = self.values.copy() #potrebuju vzit ty prumerne rewardy, ale nechci modifikvoat to co je ulozeno

                explored = self.counts > 0 #hodi true pro ty co uz byly explored a false pro ty co ne
                #ok tohle jakoby udela masku
                #jde o to abych nedelila nulou tzn ignoruju ty neexplored, sem se stejne nedostanou zadny co uz nemam ve vyberu logicky
                ucb_scores[explored] += (
                    self.c
                    * np.sqrt(
                        np.log(max(self.t, 2))
                        / self.counts[explored]
                    )
                ) #tohle je strasne nepochopitelne napsany
                #pointa je spocitat teda to pro vsechny jen pro ty neprozkoumane bez toho sqrt bla bla

                remaining_scores = ucb_scores[remaining]
                #a vezmu ty nejvyssi do poctu
                #ale jen z tech ze kterych mam jeste vybirat, ty vybrany uz sou vybrany zejo
                best_local = np.argsort(
                    remaining_scores
                )[-remaining_needed:]
                #todo je to tu naopak!!
                # chosen.extend(
                #     list(remaining[best_local])
                # )
                #mein gott to je peklo
                chosen.extend(
                    list(remaining[best_local][::-1])
                )

        self.t += 1 #todo: jak je to s tim teckem v base, nedela se to teda 2x? radsi checknout

        return np.array(chosen)


# ============================================================
# THOMPSON SAMPLING
# ============================================================
#ok takze mam beta rozdeleni, co se sklada z alfa - pocet uspechu a beta - pocet neuspechu
class ThompsonSamplingAgent:

    def __init__(self, n_arms):

        self.alpha = np.ones(n_arms) #na zacatku hodim same 1

        self.beta = np.ones(n_arms) # a tady taky. tzn kazdy arm zacina s 1,1

    def select_arms(self, available_indices, k):

        samples = np.random.beta(
            self.alpha,
            self.beta
        ) #pro kazdy arm nahodne vygeneruju skore z jeho beta distribuce
        #tzn skoncim s tim ze mam treba pro 5 options 5 cisel

        available_scores = samples[available_indices] #pocitala sem to pro vsechny options, takze ted vezmu fakt jen ty co mam na vyber

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1] #snad cajk? neupravovala sem to

    #ok tady to prepisuje ten update z basu co sem se k nemu jeste nedostala skrz kod
    #todo: dostat se k tomuto skrz pusteni scenare
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
        #vezmuu skore jen pro ty, ktere mam na vyber
        stable_scores = (
            available_scores
            - available_scores.max()
        )#todo: jak si pamatuju v tehlech pripadech teda to ze ty indexy uz nemaji vsechna cisla atp???
        #od kazdeho odectu nejvyssi skore - tzn nejvyssi ma ted 0, zbytek v minusu
        exp_scores = np.exp(
            stable_scores / self.temperature
        ) #to co melo 0 ma 1.

        probs = exp_scores / exp_scores.sum() #prepocitam na pravdepodobnosti

        return np.random.choice( # a pak podle tech probls hazu kostkou
            available_indices,
            size=min(k, len(available_indices)),
            replace=False,
            p=probs
        ) #toto za me ok


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

# def main():
#
#     all_results = []
#
#     for k in CONFIG["N_SHOWN_OPTIONS_LIST"]:
#
#         print("\n" + "=" * 60)
#         print(f"TOP-K = {k}")
#         print("=" * 60)
#
#         topk_rows = []
#
#         for agent_name, agent_class in AGENTS.items():
#
#             run_rewards = []
#
#             for run in range(CONFIG["N_RUNS"]):
#
#                 mean_reward = run_experiment(
#                     agent_class,
#                     k
#                 )
#
#                 run_rewards.append(mean_reward)
#
#             mean_reward = np.mean(run_rewards)
#
#             std_reward = np.std(run_rewards)
#
#             ci95 = (
#                 1.96
#                 * std_reward
#                 / np.sqrt(CONFIG["N_RUNS"])
#             )
#
#             row = {
#
#                 "agent": agent_name,
#
#                 "top_k": k,
#
#                 "mean_reward": mean_reward,
#
#                 "std_reward": std_reward,
#
#                 "ci95": ci95,
#
#                 "min_reward": np.min(run_rewards),
#
#                 "max_reward": np.max(run_rewards),
#             }
#
#             topk_rows.append(row)
#
#         random_reward = next(
#             row["mean_reward"]
#             for row in topk_rows
#             if row["agent"] == "Random"
#         )
#
#         for row in topk_rows:
#
#             improvement = (
#                 (
#                     row["mean_reward"]
#                     - random_reward
#                 )
#                 / random_reward
#             ) * 100
#
#             row["improvement_vs_random_pct"] = improvement
#
#         topk_rows = sorted(
#             topk_rows,
#             key=lambda x: x["mean_reward"],
#             reverse=True
#         )
#
#         for rank, row in enumerate(topk_rows, start=1):
#
#             row["rank"] = rank
#
#             all_results.append(row)
#
#             print(
#                 f"{rank}. "
#                 f"{row['agent']:<20}"
#                 f"reward={row['mean_reward']:.4f} | "
#                 f"std={row['std_reward']:.4f} | "
#                 f"CI95=±{row['ci95']:.4f} | "
#                 f"improvement={row['improvement_vs_random_pct']:+.2f}%"
#             )
#
#     results_df = pd.DataFrame(all_results)
#
#     results_df = results_df[[
#         "top_k",
#         "rank",
#         "agent",
#         "mean_reward",
#         "std_reward",
#         "ci95",
#         "min_reward",
#         "max_reward",
#         "improvement_vs_random_pct"
#     ]]
#
#     print("\nFINAL RESULTS:")
#     print(results_df.to_string(index=False))
#
#
#     # ============================================================
#     # PLOT
#     # ============================================================
#
#     plt.figure(figsize=(10, 6))
#
#     for agent_name in results_df["agent"].unique():
#
#         subset = results_df[
#             results_df["agent"] == agent_name
#         ]
#
#         plt.plot(
#             subset["top_k"],
#             subset["mean_reward"],
#             marker="o",
#             label=agent_name
#         )
#
#     plt.xlabel("Number of shown alternatives (TOP-K)")
#     plt.ylabel("Mean acceptance reward")
#     plt.title("Bandit Strategy Comparison")
#     plt.legend()
#     plt.grid(True)
#     plt.show()
#
#
# if __name__ == "__main__":
#     main()
