from .base import BaseAgent
import numpy as np

class RandomAgent(BaseAgent):

    def select_arms(self, available_indices, k):

        return self.rng.choice(
            available_indices,
            size=min(k, len(available_indices)),
            replace=False
        )
