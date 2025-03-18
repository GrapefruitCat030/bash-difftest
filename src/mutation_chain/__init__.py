"""
Mutation Chain package for Shell Metamorphic Testing Framework
"""

from .chain     import MutationChain, MutateResult
from .base      import BaseMutator
from .mutres    import MutateResult

__all__ = ["MutationChain", "MutateResult", "BaseMutator", "MutateResult"]