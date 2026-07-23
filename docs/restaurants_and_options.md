# Restaurants and Options

## Restaurant Configuration

Restaurants are configured in `RESTAURANT_CONFIGS`. Each restaurant has:

- `name`: display name of the restaurant.
- `tier`: restaurant segment used to separate experiments. Current tiers are `budget`, `midrange`, and `premium`.
- `tag`: information-only compensation label. Current values are `high-compensation`, `moderate`, and `low-compensation`. The tag is currently read-only metadata and is not used by the code or statistics.
- `allowed_options`: the seven options that can be offered by that restaurant.

Every configured restaurant currently has exactly seven allowed options.

## Option Catalogue

All available options are defined in `ALL_OPTIONS`. Each option has three numeric attributes:

- `time_shift`: delay in minutes. `0` means the original reservation time is kept, `60`, `120`, and `180` represent same-day delays, and `1440` represents the same time on the next day.
- `discount`: percentage discount represented as a decimal value, for example `0.10` means 10%.
- `perk_value`: normalized value of an added perk, such as a drink, dessert, appetizer, VIP table upgrade, or priority future booking.

The option catalogue contains:

- Pure time shifts, such as `same_day_60min`.
- Next-day offers, such as `next_day_same_time` or `next_day_plus_10pct`.
- Pure discounts, such as `discount_10pct`.
- Pure perks, such as `free_drink` or `vip_table_upgrade`.
- Combined offers, such as delay plus discount, delay plus perk, or delay plus discount plus perk.

## Option Combination Rules

Restaurant option sets are curated so that a single restaurant does not contain options where one option is strictly better than another in every relevant dimension.

For example, a restaurant should not offer both `same_day_60min` and `60min_plus_5pct`, because the second option has the same delay and adds a discount. In that pair, `60min_plus_5pct` dominates `same_day_60min`.

Some combinations are still valid even when one attribute is better than another. For example, `discount_5pct` and `60min_plus_10pct` can both be present because the customer may not be available 60 minutes later. The better discount comes with a time trade-off.

Discount-only options with different discount values should not appear together for the same restaurant, because the larger discount is always better under the current representation.

Perks have fixed `perk_value` scores, but customers may still have different preferences. Technically the perks can be ranked by value, but their interpretation is more subjective than discount or delay.
## Option Usage Across Restaurants

The table below shows how many restaurant configurations include each option.

| Option                         | Usage Count |
| ------------------------------ | ----------: |
| priority_future_booking        |           7 |
| same_day_60min                 |           6 |
| discount_10pct                 |           6 |
| vip_table_upgrade              |           6 |
| next_day_same_time             |           5 |
| 120min_plus_dessert            |           5 |
| same_day_120min                |           4 |
| next_day_plus_vip              |           4 |
| discount_5pct                  |           4 |
| free_appetizer                 |           4 |
| 120min_plus_10pct_plus_drink   |           4 |
| 180min_plus_drink              |           4 |
| next_day_plus_10pct            |           3 |
| discount_15pct                 |           3 |
| same_day_180min                |           3 |
| 180min_plus_15pct              |           3 |
| 60min_plus_drink               |           3 |
| 60min_plus_15pct_plus_drink    |           3 |
| discount_20pct                 |           2 |
| free_dessert                   |           2 |
| 60min_plus_10pct               |           2 |
| 120min_plus_15pct              |           2 |
| 120min_plus_vip                |           2 |
| 180min_plus_apetizer           |           2 |
| 180min_plus_05pct_plus_dessert |           2 |
| 60min_plus_20pct               |           2 |
| 120min_plus_5pct_plus_vip      |           2 |
| next_day_plus_20pct            |           1 |
| free_drink                     |           1 |
| 120min_plus_10pct              |           1 |
| 180min_plus_20pct              |           1 |
| 60min_plus_10pct_plus_drink    |           1 |
| 180min_plus_10pct_plus_vip     |           1 |
| 120min_plus_20pct              |           1 |
| 120min_plus_5pct               |           1 |
| 180min_plus_20pct_plus_drink   |           1 |
| next_day_plus_10pct_plus_drink |           1 |
| next_day_plus_drink            |           0 |
| 60min_plus_5pct                |           0 |
| 60min_plus_5pct_plus_dessert   |           0 |

## `generate_restaurants`

`generate_restaurants(restaurant_tiers=None)` builds the runtime restaurant objects from `RESTAURANT_CONFIGS`.

When `restaurant_tiers` is `None`, the function creates all configured restaurants. When one or more tiers are passed in, it creates only restaurants whose `tier` is included in that filter.

The function first converts the tier filter to a set, then builds restaurant items in numeric `restaurant_id` order. Each item has the shape:

```python
(restaurant_id, RESTAURANT_CONFIGS[restaurant_id])
```

For every selected restaurant, the function creates a calendar. The calendar is indexed by day and hour. For each day from `0` to `CONFIG["N_DAYS"] - 1`, and for each open hour from `CONFIG["OPEN_HOUR"]` to `CONFIG["CLOSE_HOUR"] - 1`, it computes occupied slots from an occupancy ratio.

The occupancy ratio starts with `CONFIG["TIER_BASE_OCCUPANCY"][tier]`. It is then adjusted by:

- `CONFIG["EVENING_OCCUPANCY_BOOST"]` when the hour is in `CONFIG["EVENING_PEAK_HOURS"]`.
- `CONFIG["WEEKEND_OCCUPANCY_BOOST"]` when the day is in `CONFIG["WEEKEND_DAYS"]`.
- Random normal noise from `np.random.normal(0, 0.08)`.

After these adjustments, the ratio is clipped to the interval from `0.05` to `1.00`. This prevents impossible occupancy values, such as a peak-hour value above 100%. The final number of occupied slots is:

```python
int(occupancy_ratio * CONFIG["SLOTS_PER_HOUR"])
```

The function also stores `calendar[CONFIG["N_DAYS"]] = calendar[0]`. This extra day repeats day `0` so that a customer requesting the last modeled day can still receive a next-day option and availability can be checked. In practical terms, the next Monday is treated as the same occupancy pattern as the previous Monday.

Each generated restaurant object contains:

- `restaurant_id`
- `name`
- `tier`
- `allowed_options`
- `calendar`
- `open_hour`
- `close_hour`
