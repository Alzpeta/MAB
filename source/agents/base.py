import numpy as np
from ..config import CONFIG

class BaseAgent:

    def __init__(self, n_arms):

        self.counts = np.zeros(n_arms) # 0 0 0 0 0 0 0 0
        self.values = ( # 0.15 0.15 0.15
            np.ones(n_arms)
            * CONFIG["INITIAL_ACCEPTANCE_ESTIMATE"]
        )

    def update(self, arm, reward):

        self.counts[arm] += 1 #not how many times we selected it, but how many times it was shown

        n = self.counts[arm]

        self.values[arm] += (
            reward - self.values[arm]
        ) / n
