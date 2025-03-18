import tree_sitter
from typing import Dict
from .mutres import MutateResult

class BaseMutator:
    def __init__(self):
        self.priority = 100  # 默认优先级，值越小优先级越高
    
    def get_name(self) -> str:
        return self.__class__.__name__
        
    def can_transform(self, node: tree_sitter.Node, source_bytes: bytes, context: Dict) -> bool:
        raise NotImplementedError
        
    def transform(self, node: tree_sitter.Node, source_bytes: bytes, 
                  context: Dict, children_results: Dict[int, MutateResult]) -> MutateResult:
        """
        转换节点
        
        参数:
            node: 当前节点
            source_bytes: 源代码字节
            context: 全局上下文
            children_results: 子节点的转换结果，键为子节点索引
            
        返回:
            MutateResult: 转换结果
        """
        raise NotImplementedError