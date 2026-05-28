from .base import BaseAgent
import numpy as np

class UCB1Agent(BaseAgent):

    def __init__(self, n_arms, c=1):

        super().__init__(n_arms)

        self.c = c
        self.t = 1


    def select_arms(self, available_indices, k):

        available_indices = np.array(available_indices)

        unexplored = np.array([
            arm for arm in available_indices
            if self.counts[arm] == 0
        ])

        chosen = []

        if len(unexplored) > 0:

            chosen.extend(
                list(unexplored[:k])
            )

        remaining_needed = k - len(chosen)

        if remaining_needed > 0:

            remaining = np.array([
                arm for arm in available_indices
                if arm not in chosen
            ])

            if len(remaining) > 0:

                ucb_scores = self.values.copy()

                explored = self.counts > 0

                ucb_scores[explored] += (
                    self.c
                    * np.sqrt(
                        np.log(max(self.t, 2))
                        / self.counts[explored]
                    )
                )

                remaining_scores = ucb_scores[remaining]

                best_local = np.argsort(
                    remaining_scores
                )[-remaining_needed:]
                #todo
                # chosen.extend(
                #     list(remaining[best_local])
                # )
                chosen.extend(
                    list(remaining[best_local][::-1])
                )

        self.t += 1

        return np.array(chosen)