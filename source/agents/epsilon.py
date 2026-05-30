import numpy as np

from .base import BaseAgent

class EpsilonGreedyAgent(BaseAgent):

    def __init__(self, n_arms, epsilon=0.1):

        super().__init__(n_arms)

        self.epsilon = epsilon

    def select_arms(self, available_indices, k):

        if np.random.rand() < self.epsilon:

            return np.random.choice(
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
        epsilon_0=0.1,
        min_epsilon=0.01
    ):

        super().__init__(n_arms)

        self.epsilon_0 = epsilon_0
        self.min_epsilon = min_epsilon

        self.t = 1

    def select_arms(self, available_indices, k):

        epsilon = max(
            self.min_epsilon,
            self.epsilon_0 / np.sqrt(self.t)
        )

        self.t += 1

        if np.random.rand() < epsilon:

            return np.random.choice(
                available_indices,
                size=min(k, len(available_indices)),
                replace=False
            )

        available_scores = self.values[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1]