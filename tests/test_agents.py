import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tests.mab_agents_imports as mab


def test_base_agent_update_tracks_counts_and_incremental_average():
    agent = mab.BaseAgent(n_arms=3)

    agent.update(arm=1, reward=1)
    agent.update(arm=1, reward=0)

    assert agent.counts.tolist() == [0, 2, 0]
    assert agent.values[1] == 0.5
    assert agent.values[0] == mab.CONFIG["INITIAL_ACCEPTANCE_ESTIMATE"]
    assert agent.values[2] == mab.CONFIG["INITIAL_ACCEPTANCE_ESTIMATE"]


def test_random_agent_selects_without_replacement_and_respects_k(monkeypatch):
    agent = mab.RandomAgent(n_arms=5)
    available_indices = np.array([1, 2, 3])

    def fake_choice(values, size, replace):
        assert values is available_indices
        assert size == 2
        assert replace is False
        return np.array([3, 1])

    monkeypatch.setattr(mab.np.random, "choice", fake_choice)

    selected = agent.select_arms(available_indices, k=2)

    assert selected.tolist() == [3, 1]


def test_random_agent_does_not_request_more_arms_than_available(monkeypatch):
    agent = mab.RandomAgent(n_arms=5)
    available_indices = np.array([1, 2])

    def fake_choice(values, size, replace):
        assert size == len(available_indices)
        return np.array([2, 1])

    monkeypatch.setattr(mab.np.random, "choice", fake_choice)

    selected = agent.select_arms(available_indices, k=5)

    assert selected.tolist() == [2, 1]


def test_fixed_order_policy_selects_first_available_arms_without_learning():
    policy = mab.FixedOrderPolicy(n_arms=5)
    available_indices = np.array([4, 1, 3])

    assert policy.select_arms(available_indices, k=1).tolist() == [4]
    assert policy.select_arms(available_indices, k=5).tolist() == [4, 1, 3]

    policy.update(arm=4, reward=1)

    assert policy.select_arms(available_indices, k=2).tolist() == [4, 1]


def test_epsilon_greedy_agent_exploits_highest_available_values():
    agent = mab.EpsilonGreedyAgent(n_arms=5)
    agent.values = np.array([0.1, 0.8, 0.4, 0.9, 0.2])
    available_indices = np.array([0, 1, 2, 4])

    selected = agent.select_arms(available_indices, k=2)

    assert selected.tolist() == [1, 2]


def test_epsilon_greedy_agent_explores_when_random_value_is_below_epsilon(
    monkeypatch,
):
    agent = mab.EpsilonGreedyAgent(n_arms=5, epsilon=1)
    available_indices = np.array([0, 1, 2])

    monkeypatch.setattr(mab.np.random, "rand", lambda: 0.0)
    monkeypatch.setattr(
        mab.np.random,
        "choice",
        lambda values, size, replace: np.array([2, 0]),
    )

    selected = agent.select_arms(available_indices, k=2)

    assert selected.tolist() == [2, 0]


def test_decay_epsilon_agent_increments_time_and_exploits_when_not_exploring(
    monkeypatch,
):
    agent = mab.DecayEpsilonAgent(n_arms=5)
    agent.values = np.array([0.1, 0.8, 0.4, 0.9, 0.2])
    agent.t = 10000
    available_indices = np.array([0, 1, 2, 4])

    monkeypatch.setattr(mab.np.random, "rand", lambda: 0.5)

    selected = agent.select_arms(available_indices, k=2)

    assert selected.tolist() == [1, 2]
    assert agent.t == 10001


def test_ucb1_agent_prioritizes_unexplored_available_arms():
    agent = mab.UCB1Agent(n_arms=5)
    agent.counts = np.array([3, 0, 2, 0, 1])
    available_indices = np.array([0, 1, 2, 3])

    selected = agent.select_arms(available_indices, k=2)

    assert selected.tolist() == [1, 3]
    assert agent.t == 2


def test_ucb1_agent_uses_scores_for_remaining_slots_after_unexplored_arms():
    agent = mab.UCB1Agent(n_arms=5)
    agent.counts = np.array([3, 0, 2, 5, 1])
    agent.values = np.array([0.3, 0.1, 0.9, 0.5, 0.2])
    available_indices = np.array([0, 1, 2, 3])

    selected = agent.select_arms(available_indices, k=3)

    assert selected.tolist() == [1, 2, 3]


def test_thompson_sampling_agent_update_adjusts_alpha_and_beta():
    agent = mab.ThompsonSamplingAgent(n_arms=3)

    agent.update(arm=1, reward=1)

    assert agent.alpha.tolist() == [1, 2, 1]
    assert agent.beta.tolist() == [1, 1, 1]

    agent.update(arm=1, reward=0)

    assert agent.alpha.tolist() == [1, 2, 1]
    assert agent.beta.tolist() == [1, 2, 1]


def test_thompson_sampling_agent_selects_highest_sampled_available_arms(
    monkeypatch,
):
    agent = mab.ThompsonSamplingAgent(n_arms=5)
    available_indices = np.array([0, 2, 4])

    monkeypatch.setattr(
        mab.np.random,
        "beta",
        lambda alpha, beta: np.array([0.1, 0.9, 0.3, 0.8, 0.2]),
    )

    selected = agent.select_arms(available_indices, k=2)

    assert selected.tolist() == [2, 4]


def test_softmax_agent_selects_with_probabilities_from_available_values(
    monkeypatch,
):
    agent = mab.SoftmaxAgent(n_arms=4, temperature=1)
    agent.values = np.array([0.1, 0.2, 0.3, 0.4])
    available_indices = np.array([0, 2, 3])
    captured = {}

    def fake_choice(values, size, replace, p):
        captured["values"] = values
        captured["size"] = size
        captured["replace"] = replace
        captured["p"] = p
        return np.array([3, 2])

    monkeypatch.setattr(mab.np.random, "choice", fake_choice)

    selected = agent.select_arms(available_indices, k=2)

    expected_scores = agent.values[available_indices]
    expected_exp_scores = np.exp(expected_scores - expected_scores.max())
    expected_probs = expected_exp_scores / expected_exp_scores.sum()

    assert selected.tolist() == [3, 2]
    assert captured["values"] is available_indices
    assert captured["size"] == 2
    assert captured["replace"] is False
    assert np.allclose(captured["p"], expected_probs)
