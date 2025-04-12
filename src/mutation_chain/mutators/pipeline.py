from typing import Any, Dict, Optional, Tuple
from src.mutation_chain import BaseMutator

class PipelineMutator(BaseMutator):
    NAME = "pipeline_mutator"
    DESCRIPTION = "将Bash Pipeline语法 |& 转换为 POSIX兼容的 2>&1 | 语法"
    TARGET_FEATURES = {"pipeline"}
    
    # 在Bash的tree-sitter语法中，|& 是一个具体的节点类型
    target_node_types = ["|&"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash Pipeline |& 语法转换为POSIX兼容代码 (cmd1 |& cmd2 -> cmd1 2>&1 | cmd2)
        
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
        
        # 遍历AST，收集所有 |& 节点
        def _traverse(node):
            if node.type in self.target_node_types:
                # 直接替换 |& 为 2>&1 |
                patches.append((node.start_byte, node.end_byte, "2>&1 |"))
            
            for child in node.children:
                _traverse(child)
        
        if root:
            _traverse(root)
        
        # 更新上下文信息
        transformed_features = context.get('transformed_features', set())
        transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        # 应用补丁并返回结果
        return self.apply_patches(source_code, patches), context