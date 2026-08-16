from .random import RandomAgent
from .epsilon import EpsilonGreedyAgent, DecayEpsilonAgent
from .ucb import UCB1Agent
from .thompson import ThompsonSamplingAgent
from .softmax import SoftmaxAgent
from .fixed_order import FixedOrderPolicy
from .oracle import OraclePolicy

AGENTS = {

    "Random": RandomAgent,

    "EpsilonGreedy": EpsilonGreedyAgent,

    "DecayEpsilon": DecayEpsilonAgent,

    "UCB1": UCB1Agent,

    "Thompson": ThompsonSamplingAgent,

    "Softmax": SoftmaxAgent,

    "FixedOrder": FixedOrderPolicy,

    "Oracle": OraclePolicy,
}

__all__ = [
    "RandomAgent",
    "EpsilonGreedyAgent",
    "DecayEpsilonAgent",
    "UCB1Agent",
    "ThompsonSamplingAgent",
    "SoftmaxAgent",
    "FixedOrderPolicy",
    "OraclePolicy",
    "AGENTS",
]
