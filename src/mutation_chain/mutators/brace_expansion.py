from src.mutation_chain import BaseMutator
import tree_sitter
from typing import Any, Dict, Optional, Tuple, List
import re

class BraceExpansionMutator(BaseMutator):
    NAME = "brace_expansion_mutator"
    DESCRIPTION = "将Bash BraceExpansion 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"BraceExpansion"}
    
    # In tree-sitter-bash, brace expansions have this node type
    target_node_types = ["brace_expression"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash BraceExpansion 语法转换为POSIX兼容代码
        
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
        
        # 遍历AST，查找所有目标节点
        self._traverse_and_collect(root, source_code, patches)
        
        # 更新上下文信息
        transformed_features = context.get('transformed_features', set())
        transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        # 应用补丁并返回结果
        return self.apply_patches(source_code, patches), context
    
    def _traverse_and_collect(self, node: tree_sitter.Node, source_code: str, patches: List):
        """递归遍历AST，收集所有需要替换的节点"""
        if node.type in self.target_node_types:
            # 检查这是否为我们要处理的数字序列格式 {a..b}
            node_text = source_code[node.start_byte:node.end_byte]
            posix_code = self._generate_posix_code(node, node_text)
            if posix_code:  # 只有成功生成POSIX代码时才添加补丁
                patches.append((node.start_byte, node.end_byte, posix_code))
        
        # 继续遍历子节点
        for child in node.children:
            self._traverse_and_collect(child, source_code, patches)
    
    def _generate_posix_code(self, node: tree_sitter.Node, node_text: str) -> str:
        """
        根据具体节点生成POSIX代码
        
        Args:
            node: tree-sitter节点
            node_text: 节点对应的源代码文本
            
        Returns:
            转换后的POSIX兼容代码，如果不是目标格式则返回None
        """
        # 使用正则表达式匹配 {a..b} 格式，其中a和b是整数
        match = re.match(r'^\{(-?\d+)\.\.(-?\d+)\}$', node_text)
        if not match:
            return None  # 不是我们要处理的数字序列格式
        
        start = int(match.group(1))
        end = int(match.group(2))
        
        # 确定序列方向（递增或递减）
        if start <= end:  # 递增序列
            return f"$(seq {start} {end})"
        else:  # 递减序列
            return f"$(seq {start} -1 {end})"