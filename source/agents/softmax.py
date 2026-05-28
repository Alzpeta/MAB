from .base import BaseAgent
import numpy as np

class SoftmaxAgent(BaseAgent):

    def __init__(self, n_arms, temperature=0.1):

        super().__init__(n_arms)

        self.temperature = temperature

    def select_arms(self, available_indices, k):

        available_scores = self.values[available_indices]

        stable_scores = (
            available_scores
            - available_scores.max()
        )

        exp_scores = np.exp(
            stable_scores / self.temperature
        )

        probs = exp_scores / exp_scores.sum()

        return np.random.choice(
            available_indices,
            size=min(k, len(available_indices)),
            replace=False,
            p=probs
        )
