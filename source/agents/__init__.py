from .random import RandomAgent
from .epsilon import EpsilonGreedyAgent, DecayEpsilonAgent
from .ucb import UCB1Agent
from .thompson import ThompsonSamplingAgent
from .softmax import SoftmaxAgent
from .fixed_order import FixedOrderPolicy

AGENTS = {

    "Random": RandomAgent,

    "EpsilonGreedy": EpsilonGreedyAgent,

    "DecayEpsilon": DecayEpsilonAgent,

    "UCB1": UCB1Agent,

    "Thompson": ThompsonSamplingAgent,

    "Softmax": SoftmaxAgent,

    "FixedOrder": FixedOrderPolicy,
}

__all__ = [
    "RandomAgent",
    "EpsilonGreedyAgent",
    "DecayEpsilonAgent",
    "UCB1Agent",
    "ThompsonSamplingAgent",
    "SoftmaxAgent",
    "FixedOrderPolicy",  # zmena
    "AGENTS",
]
