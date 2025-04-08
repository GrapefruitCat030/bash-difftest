
import logging
from typing import List
from .base import BaseMutator


class MutatorChain:
    """
    转换器链，用于管理和执行一系列Shell代码转换器
    
    工作流程:
    code1[包含A,B,C特性] -> 转换器A -> code2[B,C特性+A'语法]
                      -> 转换器B -> code3[C特性+A',B'语法]
                      -> 转换器C -> code4[A',B',C'语法]
    """
    
    def __init__(self):
        self.mutators: List[BaseMutator] = []
        self.logger = logging.getLogger("mutator-chain")
        self.logger.setLevel(logging.INFO)

    def register(self, mutator: BaseMutator) -> 'MutatorChain':
        if not isinstance(mutator, BaseMutator):
            raise TypeError("mutator must be an instance of BaseMutator")
        self.mutators.append(mutator)
        return self
    
    def register_all(self, mutators: List[BaseMutator]) -> 'MutatorChain':
        for mutator in mutators:
            self.register(mutator)
        return self
    
    def transform(self, source_code: str) -> str:
        """
        对输入代码应用转换链中的所有转换器
        
        Args:
            source_code: 原始shell代码
                
        Returns:
            转换后的shell代码
        """
        result = source_code
        context = {}  # 初始空上下文
        
        for i, mutator in enumerate(self.mutators):
            result, context = mutator.transform(result, context)

        return result
    
    def set_debug(self, enabled: bool = True) -> 'MutatorChain':
        self.logger.setLevel(logging.DEBUG if enabled else logging.INFO)
        return self
    
    def reset(self) -> 'MutatorChain':
        self.mutators.clear()
        return self
    
    def get_mutators(self) -> List[BaseMutator]:
        return self.mutators.copy()