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
        """初始化一个空的转换器链"""
        self.mutators: List[BaseMutator] = []
        self.debug_mode: bool = False
    
    def register(self, mutator: BaseMutator) -> 'MutatorChain':
        """注册一个转换器到链上"""
        if not isinstance(mutator, BaseMutator):
            raise TypeError("转换器必须是BaseMutator的实例")
        self.mutators.append(mutator)
        return self
    
    def register_all(self, mutators: List[BaseMutator]) -> 'MutatorChain':
        """批量注册多个转换器"""
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
            if self.debug_mode:
                print(f"[{i+1}/{len(self.mutators)}] 应用转换器: {mutator.__class__.__name__}")
            
            result, context = mutator.transform(result, context)
            
            if self.debug_mode:
                # 可以在这里输出上下文中的关键信息
                if context and 'transformed_features' in context:
                    print(f"  转换特性: {context['transformed_features']}")
        
        return result
    
    def set_debug(self, enabled: bool = True) -> 'MutatorChain':
        """设置调试模式"""
        self.debug_mode = enabled
        return self
    
    def reset(self) -> 'MutatorChain':
        """重置转换链，清除所有已注册的转换器"""
        self.mutators.clear()
        return self
    
    def get_mutators(self) -> List[BaseMutator]:
        """获取当前注册的所有转换器"""
        return self.mutators.copy()