# Requested Experiments

| Experiment | Configuration change | ExperimentConfig keys used |
| --- | --- | --- |
| Baseline run | Use the default configuration. | None (default values). |
| Higher occupancy | Increase `TIER_BASE_OCCUPANCY`. | `TIER_BASE_OCCUPANCY` |
| Lower occupancy | Decrease `TIER_BASE_OCCUPANCY`. | `TIER_BASE_OCCUPANCY` |
| More optimistic initial estimate | Increase `INITIAL_ACCEPTANCE_ESTIMATE`. | `INITIAL_ACCEPTANCE_ESTIMATE` |
| More positive customer mood | Increase `BASE_UTILITY`. | `BASE_UTILITY` |
| Noisy reward environment | Increase observation noise in outcomes. | `NOISE_STD` |
| Extended operating hours | Expand the daily opening window. | `OPEN_HOUR`, `CLOSE_HOUR` |

Higher occupancy = {"budget": 0.60, "midrange": 0.75, "premium": 0.90}
Lower occupancy = {"budget": 0.30, "midrange": 0.45, "premium": 0.60}
More optimistic initial estimate  = 0.55
More positive customer mood = 0
Noisy reward environment = 1
Extended operating hours = OPEN_HOUR =13 CLOSE_HOUR=21

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

## Fairness Between Agents

The problem is whether different agents may receive different generated options because of randomness.

### Needs Decision

If each agent gets separately generated restaurants, customers, or availability conditions, then comparison between agents may include random environment differences.

For a stricter comparison, all agents in the same scenario should probably share the same generated restaurants and customers, or use controlled seeds.

The current function generates restaurants and customers inside each experiment call, so this should be checked when comparing strategies.

## Empty Available Options

Both experiment functions handle zero available options by displaying an empty array.

```python
displayed_arms = np.array([])
```

### Needs Decision

This case is connected to the reservation environment behavior. If no options are displayed, the environment returns no chosen arm and reward `0`.

We should decide whether this should count as a failed interaction, or whether the customer should be skipped because the agent had no valid action.
