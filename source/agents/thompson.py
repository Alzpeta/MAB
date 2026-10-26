import numpy as np

class ThompsonSamplingAgent:

    def __init__(self, n_arms, rng=None):

        self.alpha = np.ones(n_arms)

        self.beta = np.ones(n_arms)
        self.rng = np.random if rng is None else rng

    def select_arms(self, available_indices, k):

        samples = self.rng.beta(
            self.alpha,
            self.beta
        )

        available_scores = samples[available_indices]

        best_local = np.argsort(
            available_scores
        )[-k:]

        return available_indices[best_local][::-1]

    def update(self, arm, reward):

        self.alpha[arm] += reward

        self.beta[arm] += 1 - reward
