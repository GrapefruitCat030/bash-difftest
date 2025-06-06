import tree_sitter
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

class BaseMutator(ABC):
    #  be overridden by subclasses
    NAME = "base_transformer"  # 转换器名称
    DESCRIPTION = "基础转换器"  # 转换器描述
    TARGET_FEATURES = set()    # 目标Bash特性集合
    
    def __init__(self, parser=None):
        self.parser = parser or initialize_parser()

    @abstractmethod
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Core method: parse AST and replace code
        
        Args:
            source_code: 需要转换的源代码
            context: 可选的上下文信息，包含前序转换器的信息
            
        Returns:
            转换后的代码和更新后的上下文信息
        """
        # patches = []
        # ast = self.parser.parse(bytes(source_code, "utf8"))
        # ...
        # return self.apply_patches(source_code, patches), context
        pass

    def apply_patches(self, source_code: str, patches: list) -> str:
        """Apply code replacement patches (shared logic for all mutators)"""
        patches.sort(reverse=True, key=lambda x: x[0])
        for start, end, replacement in patches:
            source_code = source_code[:start] + replacement + source_code[end:]
        return source_code