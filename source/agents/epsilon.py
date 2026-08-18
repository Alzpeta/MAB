import numpy as np

from .base import BaseAgent

class EpsilonGreedyAgent(BaseAgent):

    def __init__(self, n_arms, epsilon=0.1, rng=None):

        super().__init__(n_arms, rng=rng)

        self.epsilon = epsilon

    def select_arms(self, available_indices, k):

        if self.rng.random() < self.epsilon:

            return self.rng.choice(
                available_indices,
                size=min(k, len(available_indices)),
                replace=False
            )

        available_scores = self.values[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1]


class DecayEpsilonAgent(BaseAgent):

    def __init__(
        self,
        n_arms,
        epsilon_0=1.0,
        min_epsilon=0.01,
        rng=None,
    ):

        super().__init__(n_arms, rng=rng)

        self.epsilon_0 = epsilon_0
        self.min_epsilon = min_epsilon

        self.t = 1

    def select_arms(self, available_indices, k):

        epsilon = max(
            self.min_epsilon,
            self.epsilon_0 / np.sqrt(self.t)
        )

        self.t += 1

        if self.rng.random() < epsilon:

            return self.rng.choice(
                available_indices,
                size=min(k, len(available_indices)),
                replace=False
            )

        available_scores = self.values[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1]
