# Customers

## `generate_customers`

`generate_customers(restaurants)` creates `CONFIG["N_CUSTOMERS"]` synthetic customers for one simulation run.

For each `customer_id`, the function:

1. Selects one restaurant from the provided `restaurants` list.
2. Creates the requested reservation day and hour.
3. Samples customer preference attributes from normal distributions.
4. Samples the group size from an explicit probability distribution.
5. Stores all generated values in a customer dictionary.

The generated list is then returned and used by the reservation environment.

## Restaurant Selection

Each customer is currently assigned to a random restaurant:

```python
restaurant = np.random.choice(restaurants)
```

This means every restaurant in the active experiment has the same probability of receiving a customer.

The current implementation keeps restaurant choice uniform even though
premium restaurants have higher base occupancy.

## Requested Time

Each customer receives a requested day and hour sampled from weighted distributions:

- `requested_day` is drawn from `0` to `CONFIG["N_DAYS"] - 1` with weekend days weighted more heavily.
- `requested_hour` is drawn from `CONFIG["OPEN_HOUR"]` to `CONFIG["CLOSE_HOUR"] - 1` with evening peak hours weighted more heavily.

This keeps the customer arrival model aligned with the restaurant occupancy model. Peak days and peak hours now attract more requests, which matches the higher occupancy used in `source/restaurants.py`.

## Customer Attributes

The behavioral attributes are sampled from normal distributions configured in `source/config.py` and clipped to the interval `[0, 1]`.

| Field | Meaning |
| --- | --- |
| `discount_affinity` | How strongly the customer values discounts. |
| `time_flexibility` | How tolerant the customer is toward a reservation delay. |
| `restaurant_loyalty` | How loyal or tolerant the customer is toward the restaurant they selected. |
| `perk_affinity` | How strongly the customer values perks such as drinks, desserts, appetizers, VIP upgrades, or priority future booking. |
| `urgency` | How urgent the customer's situation is. Higher urgency makes delays more painful. |

`restaurant_loyalty` is attached to the restaurant the customer is currently trying to visit. This is intentional: the customer is loyal to the selected restaurant in the current scenario, not to a separate global restaurant identity.

## Group Size

### Changed

Group size was changed from a simple uniform random integer to an explicit probability distribution.

Previous approach:

```python
np.random.randint(1, 7)
```

Current approach:

```python
np.random.choice(
    [1, 2, 3, 4, 5, 6, 7],
    p=[0.15, 0.35, 0.2, 0.12, 0.1, 0.05, 0.03]
)
```

This is more realistic because a group of two people should not be as likely as a group of seven people.

### Why This Matters

Group size is now important in availability checks. The simulation checks whether the restaurant has enough remaining capacity for the whole group:

```python
restaurant["calendar"][day][hour] + group_size <= CONFIG["SLOTS_PER_HOUR"]
```

This means an option can be unavailable for a larger group even when it would be available for a smaller group.

## How Customer Fields Affect Acceptance

Customer attributes are used later by the acceptance model.

- Discounts increase utility through `discount_affinity`.
- Time shifts reduce utility more when `time_flexibility` is low.
- Urgency adds another delay penalty. Flexibility is treated as a personality trait, while urgency is treated as a situational state.
- Perks increase utility through `perk_affinity`.
- Loyalty adds a small positive utility boost through `restaurant_loyalty`.
- Evening reservations are less flexible, so delays after `19:00` receive an extra penalty.
- Larger groups are less tolerant of delays, so groups of size `5` or more receive an extra delay penalty.

The model also adds random behavioral noise before converting utility into an acceptance probability.
