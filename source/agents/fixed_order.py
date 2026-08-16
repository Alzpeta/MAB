import numpy as np


class FixedOrderPolicy:

    def __init__(self, n_arms):
        # accepts the common constructor signature but stores no learned state.
        pass

    def select_arms(self, available_indices, k):
        # return the first feasible offers in their existing order.
        return np.array(available_indices[:min(k, len(available_indices))])

    def update(self, arm, reward):
        # this fixed baseline intentionally does not learn from outcomes.
        del arm, reward
