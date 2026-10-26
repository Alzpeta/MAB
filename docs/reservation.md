# Reservation

Reservation logic is stored in `source/reservation.py`. This module connects customers, restaurant capacity, available compensation options, and the simulated customer decision.

The flow is:

1. Check whether a restaurant has enough capacity for a customer's group.
2. Filter the restaurant's allowed options to only the options that are actually available for the requested time.
3. Estimate the customer's probability of accepting each displayed option.
4. Let the reservation environment return a reward to the bandit agent.

## `has_capacity`

`has_capacity(restaurant, day, hour, group_size)` checks whether the restaurant can fit the whole group at a specific day and hour.

The check is:

```python
restaurant["calendar"][day][hour] + group_size <= CONFIG["SLOTS_PER_HOUR"]
```

This means the current number of occupied seats plus the incoming group size must be less than or equal to the hourly slot capacity.

Group size matters here directly. A time slot can be available for a group of two but unavailable for a group of six.

## `get_available_options`

`get_available_options(customer)` returns only the options from the customer's selected restaurant that can actually be offered.

Each allowed option is looked up in `ALL_OPTIONS`. Its `time_shift` is converted from minutes to whole hours:

```python
time_shift = int(np.ceil(arm["time_shift"] / 60))
```

Options with minute-level shifts are effectively rounded up to whole hours. For example, a hypothetical 45-minute delay would be treated as a one-hour delay.

## Same-Day Options

For same-day options, the function computes:

```python
future_hour = hour + time_shift
```

The option is skipped when:

- the shifted reservation would be at or after the restaurant closing hour
- the shifted hour does not have enough capacity for the full group

This means the model does not offer a same-day delay if it would move the customer outside opening hours.

## Next-Day Options

For next-day options, `time_shift == 24` is treated specially.

The model checks the same requested hour on the next day:

```python
day + 1
hour
```

This is safe because the original requested hour already had to be within opening hours. Therefore, the same hour on the next day should also be within opening hours.


The current restaurant generation handles this by adding one extra day that repeats day `0`:

```python
calendar[CONFIG["N_DAYS"]] = calendar[0]
```

So if `N_DAYS == 7`, day `7` exists as a repeated version of day `0`.

## Availability Risk

For example, an experiment might ask the agent to show five options, but capacity and opening-hour checks may leave only three valid options.

The current code simply returns the available options it finds. The later environment behavior depends on what the agent ultimately displays.

## `option_names_to_indices`

`option_names_to_indices(option_names)` converts option names into numeric arm indices:

```python
OPTION_NAMES.index(name)
```

This is needed because the bandit agents operate on arm indices, while restaurant configuration and option definitions use readable option names.

## `compute_acceptance_probability`

`compute_acceptance_probability(customer, option_name)` estimates how likely a customer is to accept a displayed option.

The model starts from `CONFIG["BASE_UTILITY"]` and then adds or subtracts utility based on the customer and the offer.

At the end, the utility is converted into a probability using a sigmoid:

```python
probability = 1 / (1 + np.exp(-utility))
```

The probability is then clipped between `MIN_ACCEPTANCE_PROBABILITY` and `MAX_ACCEPTANCE_PROBABILITY` so the model is not fully deterministic.

## Time Shift Normalization

Time shift is measured in minutes, while the other utility inputs are normalized values around `0` to `1`.

The model therefore normalizes the shift:

```python
normalized_shift = arm["time_shift"] / CONFIG["TIME_SHIFT_NORMALIZER"]
```

Currently, `TIME_SHIFT_NORMALIZER` is one full day in minutes.

## Utility Components

The acceptance model uses these effects:

| Component | Effect |
| --- | --- |
| `BASE_UTILITY` | Starting willingness to accept an alternative offer. |
| `discount_affinity * discount` | Customers who like discounts value discounted offers more. |
| `time_flexibility` | Less flexible customers are penalized more for delays. |
| `urgency` | Urgent situations make delays more painful. |
| `perk_affinity * perk_value` | Customers who like perks value free extras or upgrades more. |
| `restaurant_loyalty` | Loyal customers receive a small positive utility boost. |
| evening request | Reservations from `19:00` onward receive an extra delay penalty. |
| large group | Groups of size `5` or more receive an extra delay penalty. |
| random noise | Adds non-determinism to customer behavior. |

### Discounts

Discounts only increase utility:

```python
customer["discount_affinity"] * arm["discount"] * CONFIG["DISCOUNT_WEIGHT"]
```

Customers with higher `discount_affinity` are more likely to accept discounted offers.

### Time Flexibility

Time flexibility is treated as a customer personality trait.

`0` means the customer is not flexible. `1` means the customer is very flexible.

The delay penalty is stronger when flexibility is low:

```python
(1 - customer["time_flexibility"]) * (-normalized_shift)
```

When the customer is fully flexible, almost nothing is subtracted for delay through this component.

### Urgency

Urgency is treated as a situational state, not a personality trait.

`0` means the customer is relaxed about the situation. `1` means the reservation is very important.

Urgency creates another delay penalty:

```python
customer["urgency"] * (-normalized_shift) * CONFIG["URGENCY_DELAY_WEIGHT"]
```

### Perks

Perks only increase utility:

```python
customer["perk_affinity"] * arm["perk_value"] * CONFIG["PERK_WEIGHT"]
```

This captures how much the customer can be persuaded by free extras, upgrades, or similar compensation.

### Loyalty

Restaurant loyalty adds a small positive utility boost:

```python
customer["restaurant_loyalty"] * CONFIG["LOYALTY_WEIGHT"]
```

This means loyal customers are slightly more tolerant of alternative offers from the restaurant they wanted.

### Evening Penalty

If the requested reservation hour is `19:00` or later, the customer receives an extra delay penalty.

The assumption is that evening reservations are less flexible.

### Group Penalty

If the group size is `5` or more, the customer receives an extra delay penalty.

The assumption is that moving a reservation is more irritating for larger groups because more people need to adjust.

### Random Noise

The model adds normally distributed random noise around zero:

```python
np.random.normal(0, CONFIG["NOISE_STD"])
```

This makes decisions less mechanical. A weak offer can occasionally be accepted, and a strong offer can occasionally be rejected.

## Probability Clipping

After the sigmoid conversion, the probability is clipped:

```python
np.clip(
    probability,
    CONFIG["MIN_ACCEPTANCE_PROBABILITY"],
    CONFIG["MAX_ACCEPTANCE_PROBABILITY"]
)
```

This prevents the model from saying that an option is literally impossible or guaranteed.

## `ReservationEnvironment`

`ReservationEnvironment` is the simulation environment used by the agents.

It stores:

- `customers`: the generated customer list
- `t`: the current time step

Each customer corresponds to one time step.

## `reset`

`reset()` sets:

```python
self.t = 0
```

This is used before a new run so the environment starts again from the first customer.

## `get_customer`

`get_customer()` returns:

```python
self.customers[self.t]
```

The current customer is therefore determined only by the current time step.

## `customer_choice`

`customer_choice(displayed_arm_indices)` simulates the customer choosing from the options displayed by the agent.

If no options are displayed, the function returns:

```python
None, 0
```

This means no arm was accepted and the reward is zero.

The current implementation treats this as a failed interaction with reward `0`.

## Acceptance Draw

The displayed options are evaluated in order.

For each option:

1. Convert the arm index back into an option name.
2. Compute the acceptance probability.
3. Draw a random number from `0` to `1`.
4. Accept the option if the random number is lower than the acceptance probability.

The relevant logic is:

```python
accepted = np.random.rand() < p_accept
```

The customer accepts the first displayed option that passes this random draw. If none of the displayed options are accepted, the function returns:

```python
None, 0
```

## Display Order Matters

Because the customer accepts the first successful option, the order of displayed options matters.

An option shown earlier gets the first chance to be accepted. This means the environment is not only modeling the set of displayed options, but also their order.

## `step`

`step(displayed_arm_indices)` performs one customer interaction.

It:

1. Calls `customer_choice(displayed_arm_indices)`.
2. Advances `self.t` by one.
3. Checks whether all customers have been processed.
4. Returns the chosen arm, reward, and done flag.

The returned dictionary has this shape:

```python
{
    "chosen_arm": chosen_arm,
    "reward": reward,
    "done": done
}
```

`done` becomes `True` when the environment has processed all generated customers.
