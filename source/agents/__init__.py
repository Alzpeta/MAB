from .random import RandomAgent
from .epsilon import EpsilonGreedyAgent, DecayEpsilonAgent
from .ucb import UCB1Agent
from .thompson import ThompsonSamplingAgent
from .softmax import SoftmaxAgent
from .oracle import OraclePolicy

AGENTS = {

    "Random": RandomAgent,

    "EpsilonGreedy": EpsilonGreedyAgent,

    "DecayEpsilon": DecayEpsilonAgent,

    "UCB1": UCB1Agent,

    "Thompson": ThompsonSamplingAgent,

    "Softmax": SoftmaxAgent,

    "Oracle": OraclePolicy,
}

__all__ = [
    "RandomAgent",
    "EpsilonGreedyAgent",
    "DecayEpsilonAgent",
    "UCB1Agent",
    "ThompsonSamplingAgent",
    "SoftmaxAgent",
    "OraclePolicy",
    "AGENTS",
]
