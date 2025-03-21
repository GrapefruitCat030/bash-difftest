"""
Mutators package for Shell Metamorphic Differential Testing Framework
"""

from .array                 import ArrayMutator
from .process_substitution  import ProcessSubstitutionMutator

__all__ = ["ArrayMutator", "ProcessSubstitutionMutator"]