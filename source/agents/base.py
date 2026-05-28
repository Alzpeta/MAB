import numpy as np
from ..config import CONFIG

class BaseAgent:

    def __init__(self, n_arms):

        self.counts = np.zeros(n_arms)
        self.values = (
            np.ones(n_arms)
            * CONFIG["INITIAL_ACCEPTANCE_ESTIMATE"]
        )

    def update(self, arm, reward):

        self.counts[arm] += 1

        n = self.counts[arm]

        self.values[arm] += (
            reward - self.values[arm]
        ) / n