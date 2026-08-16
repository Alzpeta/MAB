import numpy as np

from ..options import OPTION_NAMES
from ..reservation import compute_expected_acceptance_probability


class OraclePolicy:

    def __init__(self, n_arms):
        pass

    def set_customer(self, customer):
        self.customer = customer

    def select_arms(self, available_indices, k):
        available_indices = np.array(available_indices)
        scores = np.array([
            compute_expected_acceptance_probability(
                self.customer,
                OPTION_NAMES[arm]
            )
            for arm in available_indices
        ])
        ranking = np.argsort(-scores, kind="stable")

        return available_indices[ranking[:min(k, len(available_indices))]]

    def update(self, arm, reward):
        pass
