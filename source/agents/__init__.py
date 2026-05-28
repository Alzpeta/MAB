from .random import RandomAgent
from .epsilon import EpsilonGreedyAgent, DecayEpsilonAgent
from .ucb import UCB1Agent
from .thompson import ThompsonSamplingAgent
from .softmax import SoftmaxAgent

AGENTS = {

    "Random": RandomAgent,

    "EpsilonGreedy": EpsilonGreedyAgent,

    "DecayEpsilon": DecayEpsilonAgent,

    "UCB1": UCB1Agent,

    "Thompson": ThompsonSamplingAgent,

    "Softmax": SoftmaxAgent
}

__all__ = [
    "RandomAgent",
    "EpsilonGreedyAgent",
    "DecayEpsilonAgent",
    "UCB1Agent",
    "ThompsonSamplingAgent",
    "SoftmaxAgent",
    "AGENTS",
]
