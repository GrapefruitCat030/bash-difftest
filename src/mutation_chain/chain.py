
import logging
from typing import List
from .base import BaseMutator


class MutatorChain:
    """
    转换器链,用于管理和执行一系列Shell代码转换器
    
    transform工作流程: 大小迭代嵌套 
    - 大迭代: 循环 [小迭代] 直到代码稳定或达到最大迭代次数
    - 小迭代:
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
        大小迭代嵌套转换器链
        
        Args:
            source_code: 原始shell代码
                
        Returns:
            转换后的shell代码
        """
        result = source_code
        context = {} 
        
        curr_round = 0
        max_round = 10  # 防止无限循环
        prev_result = None
        while result != prev_result and curr_round < max_round:
            prev_result = result
            curr_round += 1
            
            self.logger.debug(f"begin iteration round [ {curr_round} ] ....")
            for _, mutator in enumerate(self.mutators):
                before_transform = result
                result, context = mutator.transform(result, context)
                if before_transform != result:
                    self.logger.debug(f"apply mutator [ {mutator.__class__.__name__} ]")
            
        if curr_round >= max_round:
            self.logger.warning("Maximum iteration reached, possible infinite loop.")
        
        self.logger.debug("the chain completes transformation.")
        return result
    
    def set_debug(self, enabled: bool = True) -> 'MutatorChain':
        self.logger.setLevel(logging.DEBUG if enabled else logging.INFO)
        return self
    
    def reset(self) -> 'MutatorChain':
        self.mutators.clear()
        return self
    
    def get_mutators(self) -> List[BaseMutator]:
        return self.mutators.copy()