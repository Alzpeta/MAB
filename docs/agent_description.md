# Agent Description

The agents choose which available reservation options should be displayed to a customer.

The general flow is:

1. The reservation logic finds available option indices for the current customer.
2. The agent receives those indices and the number of options it may show, `k`.
3. The agent selects up to `k` arms.
4. The reservation environment simulates whether the customer accepts one of the displayed arms.
5. The accepted arm is updated with the observed reward.

In this project, an arm means one reservation option from `ALL_OPTIONS`.

## Agent Registry

The available agents are exposed through `source/agents/__init__.py`.

`AGENTS` maps readable strategy names to agent classes:

```python
AGENTS = {
    "Random": RandomAgent,
    "EpsilonGreedy": EpsilonGreedyAgent,
    "DecayEpsilon": DecayEpsilonAgent,
    "UCB1": UCB1Agent,
    "Thompson": ThompsonSamplingAgent,
    "Softmax": SoftmaxAgent
}
```

This allows scenario code to loop through all configured strategies without manually naming each class every time.

## Shared Input

Most agents implement:

```python
select_arms(available_indices, k)
```

where:

- `available_indices` are the option indices that can currently be offered.
- `k` is the maximum number of options the agent may display.

The agents generally return:

```python
size=min(k, len(available_indices))
```

This means if fewer than `k` options are available, the agent only returns the available number.

## `BaseAgent`

`BaseAgent` stores the shared state used by several strategies.

It initializes:

```python
self.counts = np.zeros(n_arms)
```

`counts` tracks how many times each arm has been selected and updated.

It also initializes:

```python
self.values = np.ones(n_arms) * CONFIG["INITIAL_ACCEPTANCE_ESTIMATE"]
```

`values` is the estimated average reward for each arm. It represents how good the agent currently thinks each arm is.

With the current default initial estimate, all arms start with the same expected reward.

## `BaseAgent.update`

`update(arm, reward)` updates the running average reward for the accepted arm.

The update logic is:

```python
self.counts[arm] += 1
n = self.counts[arm]
self.values[arm] += (reward - self.values[arm]) / n
```

This is an incremental average. The agent does not store all past rewards, only the count and current value estimate.

## `RandomAgent`

`RandomAgent` chooses randomly from the available arms.

The selection is:

```python
np.random.choice(
    available_indices,
    size=min(k, len(available_indices)),
    replace=False
)
```

`replace=False` means the same arm cannot be selected twice in one displayed set.

This agent does not use learned values when selecting arms. It is used as a baseline.

## `EpsilonGreedyAgent`

$$
a =
\begin{cases}
\text{RandomArm}, & \text{with probability } \epsilon \\
\arg\max_i Q_i, & \text{with probability } 1-\epsilon
\end{cases}
$$

where:

- $a$ = selected arm
- $Q_i$ = estimated reward of arm $i$
- $\epsilon$ = exploration probability


`EpsilonGreedyAgent` mixes exploration and exploitation.

It has:

```python
epsilon = 0.1
```

`epsilon` is the probability of exploration.

On each selection, the agent draws a random number between `0` and `1`.

If the draw is below `epsilon`, it explores by choosing random available arms.

If the draw is not below `epsilon`, it exploits by choosing the available arms with the highest current value estimates.

```python
available_scores = self.values[available_indices]
best_local = np.argsort(available_scores)[-k:]
return available_indices[best_local][::-1]
```

The returned indices are converted back from local positions into real arm indices.

## `DecayEpsilonAgent`


$$
\epsilon_t
=
\max
\left(
\epsilon_{\min},
\frac{\epsilon_0}{\sqrt{t}}
\right)
$$

where:

- $\epsilon_t$ = exploration probability at timestep $t$
- $\epsilon_0$ = initial exploration probability
- $\epsilon_{\min}$ = minimum exploration probability
- $t$ = current timestep


`DecayEpsilonAgent` is similar to epsilon-greedy, but the exploration probability decreases over time.

The idea is:

- explore more at the beginning
- exploit more after the agent has collected data

It starts with:

```python
epsilon_0 = 1.0
min_epsilon = 0.01
self.t = 1
```

At each selection, epsilon is computed as:

```python
epsilon = max(
    self.min_epsilon,
    self.epsilon_0 / np.sqrt(self.t)
)
```

Then `self.t` is incremented.

This means exploration decreases as `t` grows, but it never goes below `min_epsilon`.

If the agent explores, it chooses random available arms. If it exploits, it chooses the available arms with the highest current values, the same way as `EpsilonGreedyAgent`.

## `UCB1Agent`

$$
UCB_i =
Q_i +
c \sqrt{\frac{\ln t}{N_i}}
$$

where:

- $UCB_i$ = UCB score of arm $i$
- $Q_i$ = estimated reward of arm $i$
- $c$ = exploration coefficient
- $t$ = current timestep
- $N_i$ = number of times arm $i$ has been selected

`UCB1Agent` means Upper Confidence Bound.

The goal is to choose arms that have a high estimated reward, while still occasionally trying arms that are uncertain.

The conceptual score is:

```text
average reward + c * sqrt(log(t) / number_of_times_arm_was_tried)
```

where:

- `average reward` is the current value estimate for the arm.
- `c` controls the exploration bonus.
- `t` is the strategy's time step.
- `number_of_times_arm_was_tried` is stored in `counts`.

The exploration bonus is larger for arms that have been tried fewer times.

## UCB Initialization Behavior

UCB cannot divide by zero, so it first selects unexplored arms:

```python
unexplored = np.array([
    arm for arm in available_indices
    if self.counts[arm] == 0
])
```

If there are unexplored available arms, the agent chooses them first.

If more arms are still needed, it computes UCB scores for the remaining explored arms and takes the highest ones.

The code copies `self.values` before adding the UCB bonus:

```python
ucb_scores = self.values.copy()
```

This avoids modifying the stored value estimates while calculating temporary selection scores.

## UCB Time Step

`UCB1Agent` has its own `self.t`.

This is needed because the UCB formula uses time in the exploration bonus.

## `ThompsonSamplingAgent`

$$
\theta_i \sim \mathrm{Beta}(\alpha_i,\beta_i)
$$

where:

- $\theta_i$ = estimated success probability of arm $i$
- $\alpha_i$ = success count + prior
- $\beta_i$ = failure count + prior


`ThompsonSamplingAgent` uses a beta distribution for each arm.

Each arm starts with:

```python
self.alpha = np.ones(n_arms)
self.beta = np.ones(n_arms)
```

So every arm starts with a Beta(1, 1) distribution.

In this setup:

- `alpha` represents successes.
- `beta` represents failures.

At selection time, the agent samples one score for each arm:

```python
samples = np.random.beta(self.alpha, self.beta)
```

Then it filters those samples to the currently available arms:

```python
available_scores = samples[available_indices]
```

The agent returns the available arms with the highest sampled scores.

## Thompson Update

Thompson sampling overrides the standard `BaseAgent.update` behavior.

The update is:

```python
self.alpha[arm] += reward
self.beta[arm] += 1 - reward
```

If the reward is `1`, alpha increases. If the reward is `0`, beta increases.

This updates the beta distribution for the selected arm.

## `SoftmaxAgent`

`SoftmaxAgent` selects arms probabilistically based on current value estimates.

$$
P(a_i)=\frac{\exp(Q_i/\tau)}
{\sum_{j=1}^{K}\exp(Q_j/\tau)}
$$

where:

- $P(a_i)$ = probability of selecting arm $i$
- $Q_i$ = estimated value (expected reward) of arm $i$
- $K$ = number of available arms
- $\tau$ = temperature parameter


It has:

```python
temperature = 0.1
```

Temperature controls how strongly the agent prefers higher-value arms.

- Lower temperature makes the agent more greedy.
- Higher temperature makes the probabilities more spread out.

The agent first takes value estimates only for available arms:

```python
available_scores = self.values[available_indices]
```

Then it subtracts the maximum score:

```python
stable_scores = available_scores - available_scores.max()
```

This improves numerical stability before exponentiation.

Next, it computes softmax probabilities:

```python
exp_scores = np.exp(stable_scores / self.temperature)
probs = exp_scores / exp_scores.sum()
```

Finally, it samples arms without replacement using those probabilities:

```python
np.random.choice(
    available_indices,
    size=min(k, len(available_indices)),
    replace=False,
    p=probs
)
```


## Displayed Arm Order

Several agents return selected arms sorted from best to worst according to their local scoring logic.

This matters because `ReservationEnvironment.customer_choice` checks displayed arms in order and the customer accepts the first option that passes its acceptance draw.

Therefore, agents are not only choosing which options to show. They are also influencing which option gets the first chance to be accepted.

## Strategies Summary

| Agent | Main idea | Exploration behavior |
| --- | --- | --- |
| `RandomAgent` | Random baseline | Always random |
| `EpsilonGreedyAgent` | Mostly choose best known arms | Random with fixed probability `epsilon` |
| `DecayEpsilonAgent` | Start random, become more greedy | Random probability decays over time |
| `UCB1Agent` | Add uncertainty bonus to value estimates | Tries unexplored or underexplored arms |
| `ThompsonSamplingAgent` | Sample from beta distributions | Exploration happens through posterior sampling |
| `SoftmaxAgent` | Sample according to softmax probabilities | Lower-value arms can still be sampled |
