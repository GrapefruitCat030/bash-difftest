from typing import Any, Dict, Optional, Tuple, List
import tree_sitter
from src.mutation_chain import BaseMutator

class LocalVariablesMutator(BaseMutator):
    NAME = "local_variables_mutator"
    DESCRIPTION = "将Bash Local Variables 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"local_variables"}
    
    target_node_types = ["declaration_command"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash Local Variables 语法转换为POSIX兼容代码
        
        Args:
            source_code: 需要转换的源代码
            context: 可选的上下文信息，包含前序转换器的信息
            
        Returns:
            转换后的代码和更新后的上下文信息
        """
        context = context or {}
        patches = []
        
        # 解析AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # 更新上下文信息
        transformed_features = context.get('transformed_features', set())
        transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        # 应用补丁并返回结果
        return self.apply_patches(source_code, patches), context