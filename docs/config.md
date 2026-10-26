# Configuration

The main configuration is stored in `source/config.py` in the `CONFIG` dictionary.

## Experiment

#### `N_CUSTOMERS`

- Default value: `20000`
- Number of customers in one simulation run.

#### `N_RUNS`

- Default value: `100`
- Number of repeated runs for each strategy.

#### `SEED`

- Default value: `33`
- Random seed used to make results reproducible.

#### `N_SHOWN_OPTIONS_LIST`

- Default value: `[1, 2, 3, 5]`
- Numbers of alternative offers tested as shown options.

## Time

#### `N_DAYS`

- Default value: `7`
- Number of simulated days.

#### `OPEN_HOUR`

- Default value: `11`
- Restaurant opening hour.

#### `CLOSE_HOUR`

- Default value: `23`
- Restaurant closing hour.

#### `SLOTS_PER_HOUR`

- Default value: `20`
- Number of available reservation slots per hour.
- Used by capacity checks for every reservation; the whole group must fit in
  the remaining slots.

## Occupancy

#### `EVENING_PEAK_HOURS`

- Default value: `[18, 19, 20, 21]`
- Hours treated as the evening peak.

#### `EVENING_OCCUPANCY_BOOST`

- Default value: `0.20`
- Occupancy increase during the evening peak.

#### `WEEKEND_DAYS`

- Set value: `[4, 5]`
- Weekend days indexed from zero; here Friday and Saturday.

#### `WEEKEND_OCCUPANCY_BOOST`

- Default value: `0.15`
- Occupancy increase during weekend days.

#### `TIER_BASE_OCCUPANCY`

- Default value: `{"budget": 0.45, "midrange": 0.60, "premium": 0.75}`
- Base occupancy by restaurant tier.

## Bandit

#### `INITIAL_ACCEPTANCE_ESTIMATE`

- Default value: `0.15`
- Initial acceptance rate/reward estimate for each arm.

## Customer Distributions

#### `DISCOUNT_AFFINITY_MEAN`

- Default value: `0.5`
- Mean customer sensitivity to discounts.

#### `DISCOUNT_AFFINITY_STD`

- Default value: `0.2`
- Standard deviation of discount sensitivity.

#### `TIME_FLEXIBILITY_MEAN`

- Default value: `0.5`
- Mean customer time flexibility.

#### `TIME_FLEXIBILITY_STD`

- Default value: `0.2`
- Standard deviation of time flexibility.

#### `LOYALTY_MEAN`

- Default value: `0.5`
- Mean customer loyalty.

#### `LOYALTY_STD`

- Default value: `0.2`
- Standard deviation of loyalty.

#### `PERK_AFFINITY_MEAN`

- Default value: `0.5`
- Mean customer affinity for perks.

#### `PERK_AFFINITY_STD`

- Default value: `0.2`
- Standard deviation of perk affinity.

#### `URGENCY_MEAN`

- Default value: `0.5`
- Mean customer urgency.

#### `URGENCY_STD`

- Default value: `0.25`
- Standard deviation of urgency.

## Acceptance Model

#### `BASE_UTILITY`

- Default value: `-2.0`
- Default utility before offer and customer attributes are applied.
- Customers are generally expected to be reluctant, because they entered the system after their original request could not be fulfilled, so they are less likely to accept an alternative.

#### `DISCOUNT_WEIGHT`

- Default value: `3.0`
- Weight of discounts in customer decision-making.

#### `TIME_SHIFT_WEIGHT`

- Default value: `2.5`
- Weight of time shift or delay.

#### `PERK_WEIGHT`

- Default value: `1.0`
- Weight of perks.

#### `LOYALTY_WEIGHT`

- Default value: `0.1`
- Weight of customer loyalty.

#### `URGENCY_DELAY_WEIGHT`

- Default value: `2.0`
- How strongly urgent customers dislike waiting.

#### `EVENING_DELAY_PENALTY`

- Default value: `0.7`
- Additional delay penalty for evening reservations.

#### `GROUP_DELAY_PENALTY`

- Default value: `0.7`
- Additional delay penalty for larger groups.

#### `NOISE_STD`

- Default value: `0.6`
- Amount of random noise in customer decision-making.

## Normalization

#### `TIME_SHIFT_NORMALIZER`

- Default value: `1440`
- Normalizes time shift to one day in minutes.
- 24x60. Without this, time shift would use different units and the agents would be highly biased.

## Acceptance Probability Clipping

Prevents determinism so that no option is completely impossible or guaranteed to be accepted.

#### `MIN_ACCEPTANCE_PROBABILITY`

- Default value: `0.01`
- Minimum allowed probability of accepting an offer.

#### `MAX_ACCEPTANCE_PROBABILITY`

- Default value: `0.95`
- Maximum allowed probability of accepting an offer.
