# Experimental Scenarios Used in the Paper

Only the scenarios listed below are used in the paper and configured in
`run_scenarios.py`.

All experiments use:

- 20,000 customers per simulation run
- 100 independent simulation runs
- random seed 33
- all restaurant tiers together

## Baseline

The baseline uses the default model configuration:

| Parameter | Baseline value |
| --- | --- |
| Opening hours | 11:00–23:00 |
| Budget occupancy | 0.45 |
| Mid-range occupancy | 0.60 |
| Premium occupancy | 0.75 |
| Decision uncertainty (`NOISE_STD`) | 0.6 |
| Customer attitude (`BASE_UTILITY`) | -2.0 |
| Initial value estimate | 0.15 |
| Evaluated values of `k` | 1, 2, 3, 4, 5, 6, 7 |

The complete baseline output is stored in:

`mab_requested_experiments_20260604_140307_more-k`

Despite the `more-k` suffix, this is the complete baseline experiment. It
contains all results for `k = 1–7`.

The older folder `mab_requested_experiments_20260530_173123_baseline` contains
only `k = 1–3`. Those results are duplicated in the complete `more-k` folder,
so the older folder is not needed.

## Extended Opening Hours

| Scenario | Opening hours | Evaluated values of `k` | Output folder |
| --- | --- | --- | --- |
| Baseline | 11:00–23:00 | 1, 2, 3 | Baseline `more-k` folder |
| Extended | 09:00–24:00 | 1, 2, 3 | `mab_requested_experiments_20260604_205405_much_extended_operating_hours` |

The older `extended_operating_hours` output with opening hours 13:00–21:00
does not match the scenario in the paper and is not used.

## Restaurant Occupancy

The occupancy comparison is evaluated for `k = 1`.

| Scenario | Budget | Mid-range | Premium | Output folder |
| --- | ---: | ---: | ---: | --- |
| Much Lower | 0.15 | 0.30 | 0.45 | `mab_requested_experiments_20260604_205405_much_lower_occupancy` |
| Lower | 0.30 | 0.45 | 0.60 | `mab_requested_experiments_20260530_200921_lower_occupancy` |
| Baseline | 0.45 | 0.60 | 0.75 | Baseline `more-k` folder |
| Higher | 0.60 | 0.75 | 0.90 | `mab_requested_experiments_20260530_200921_higher_occupancy` |
| Much Higher | 0.75 | 0.90 | 0.98 | `mab_requested_experiments_20260604_205405_much_higher_occupancy` |

## Decision Uncertainty

Decision uncertainty is controlled by `NOISE_STD` and evaluated for
`k = 1, 2, 3`.

| Scenario | `NOISE_STD` | Output folder |
| --- | ---: | --- |
| Low | 0.1 | `mab_requested_experiments_20260606_121238_very_low_noise_environment` |
| Baseline | 0.6 | Baseline `more-k` folder |
| High | 1.0 | `mab_requested_experiments_20260530_200921_noisy_reward_environment` |
| Very High | 1.5 | `mab_requested_experiments_20260604_205405_much_noisier_reward_environment` |

The output with `NOISE_STD = 0.3` is not part of the scenarios evaluated in
the paper.

## Customer Attitude

Customer attitude is controlled by `BASE_UTILITY` and evaluated for
`k = 1, 2, 3`.

| Scenario | `BASE_UTILITY` | Output folder |
| --- | ---: | --- |
| Very Pessimistic | -3.5 | `mab_requested_experiments_20260604_205405_very_pesimistic_customer_mood` |
| Pessimistic | -2.5 | `mab_requested_experiments_20260606_175322_2.5_customer_mood` |
| Baseline | -2.0 | Baseline `more-k` folder |
| Optimistic | -1.0 | `mab_requested_experiments_20260606_175322_1_customer_mood` |
| Very Optimistic | 0.0 | `mab_requested_experiments_20260530_200921_more_positive_customer_mood` |

## Running All Paper Scenarios

Run:

```bash
python run_scenarios.py --requested-experiments
```

This executes the baseline and every non-baseline scenario listed above.

## Experiment Runner

Experiment logic is stored in `source/experiment.py`.

The module connects:

- generated restaurants
- generated customers
- the reservation environment
- available option filtering
- one selected bandit agent
- final reward calculation

In this context, one experiment means running one agent strategy through one generated customer sequence and returning the average reward.

## `run_experiment_with_option_stats`

`run_experiment_with_option_stats(agent_class, k, customers)` runs one simulation for one agent class using a pre-generated customer list.

The function initializes the reservation environment directly from the provided `customers` list:

```python
env = ReservationEnvironment(customers)
```

The selected agent is initialized with the total number of arms:

```python
agent = agent_class(N_ARMS)
```

`N_ARMS` is the number of options in `ALL_OPTIONS`.

## Experiment Loop

Each loop iteration represents one customer.

The current customer is retrieved from the environment:

```python
customer = env.get_customer()
```

Then the experiment gets only the options that are currently available for that customer:

```python
available_options = get_available_options(customer)
```

These readable option names are converted into numeric arm indices:

```python
available_indices = option_names_to_indices(available_options)
```

The bandit agents work with indices, not option names.

## Displayed Arms

If there are no available options, the experiment displays an empty array:

```python
displayed_arms = np.array([])
```

Otherwise, the agent selects up to `k` arms:

```python
displayed_arms = agent.select_arms(
    available_indices,
    k
)
```

`k` is the number of options the experiment allows the agent to show.

## Environment Step

The displayed arms are passed to the environment:

```python
result = env.step(displayed_arms)
```

The environment returns:

```python
{
    "chosen_arm": chosen_arm,
    "reward": reward,
    "done": done
}
```

The reward is stored:

```python
rewards.append(reward)
```

At the end of the experiment, the function returns:

```python
np.mean(rewards)
```

This is the average acceptance reward across all customers in the run.

## Agent Update

The agent is updated for displayed arms after each customer interaction:

```python
for arm in displayed_arms:
    if result["chosen_arm"] is None:
        agent.update(arm, 0)
    elif arm == result["chosen_arm"]:
        agent.update(arm, 1)
        break
    else:
        agent.update(arm, 0)
```

If a customer rejects all displayed options, every displayed arm receives an update with reward `0`.

If a customer accepts an option, displayed arms before the accepted option receive reward `0`, the accepted arm receives reward `1`, and the update loop stops.

This happens in `source/experiment.py`:

```python
result = env.step(displayed_arms)

reward = result["reward"]

rewards.append(reward)

for arm in displayed_arms:
    if result["chosen_arm"] is None:
        agent.update(arm, 0)
    elif arm == result["chosen_arm"]:
        agent.update(arm, 1)
        break
    else:
        agent.update(arm, 0)
```

The reward is always appended to the experiment-level results. Agent learning is based on the displayed arms and the first accepted arm, if any.

The related return value comes from `source/reservation.py`. If the customer does not accept any displayed option, `customer_choice` returns:

```python
return None, 0
```

So a full rejection becomes `chosen_arm = None` and `reward = 0`. The `0` is counted in the experiment average and is also used to update all displayed arms.


## Done Condition

The loop stops when the environment says all customers have been processed:

```python
if result["done"]:
    break
```

`run_experiment_with_option_stats(agent_class, k, customers)` runs a similar simulation, but also tracks option-level statistics.

It tracks:

```python
shown_counts = np.zeros(N_ARMS)
accepted_counts = np.zeros(N_ARMS)
```

`shown_counts` counts how many times each arm was displayed.

`accepted_counts` counts how many times each arm was accepted.

## Shown Counts

For each displayed arm, the function increments:

```python
shown_counts[arm] += 1
```

This records exposure: how often the customer saw the option.

## Accepted Counts

When a customer accepts an arm, the function increments:

```python
accepted_counts[result["chosen_arm"]] += 1
```

The agent update itself is handled by the displayed-arm update loop described above.

So the accepted option contributes both to the option statistics and to the agent's learning, while rejected displayed options contribute negative feedback.

## Option Statistics Output

After the run, the function builds one row per option.

Each row contains:

- `option_name`
- `option_category`
- `shown_count`
- `accepted_count`
- `acceptance_rate`

The acceptance rate is:

```python
accepted_count / shown_count
```

If an option was never shown, its acceptance rate is stored as `np.nan`.

The function returns:

```python
np.mean(rewards), pd.DataFrame(option_rows)
```

So the output is the average reward plus a dataframe with option-level performance.

## Empty Available Options

Both experiment functions handle zero available options by displaying an empty array.

```python
displayed_arms = np.array([])
```

This case is connected to the reservation environment behavior. If no options are displayed, the environment returns no chosen arm and reward `0`.
