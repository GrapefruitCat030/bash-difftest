from typing import Dict, Any, Optional, Tuple, Set
import tree_sitter
from src.mutation_chain import BaseMutator

class FunctionsMutator(BaseMutator):
    NAME = "functions_mutator"
    DESCRIPTION = "将Bash Functions 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"functions"}
    
    # 函数定义在tree-sitter-bash中是function_definition节点
    target_node_types = ["function_definition"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash函数定义语法转换为POSIX兼容代码
        
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
        
        # 遍历AST，收集所有function_definition节点
        def _traverse(node: tree_sitter.Node):
            if node.type in self.target_node_types:
                # 生成POSIX等效代码，并记录替换位置
                posix_code = self._generate_posix_code(node, source_code)
                patches.append((node.start_byte, node.end_byte, posix_code))
            for child in node.children:
                _traverse(child)
        
        # 执行遍历
        if root:
            _traverse(root)
        
        # 更新上下文信息
        transformed_features = context.get('transformed_features', set())
        transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        # 应用补丁并返回结果
        return self.apply_patches(source_code, patches), context
    
    def _generate_posix_code(self, node: tree_sitter.Node, source_code: str) -> str:
        """根据函数定义节点生成POSIX兼容的函数定义"""
        # 查找函数名称节点
        name_node = None
        body_start = None
        body_end = None
        
        for child in node.children:
            if child.type == "word":  # 函数名通常在word节点中
                name_node = child
            elif child.type == "compound_statement":  # 函数体
                body_start = child.start_byte
                body_end = child.end_byte
        
        if not name_node or body_start is None:
            # 如果找不到必要的组件，返回原始代码
            return source_code[node.start_byte:node.end_byte]
        
        # 提取函数名
        function_name = source_code[name_node.start_byte:name_node.end_byte]
        
        # 提取函数体内容（包括大括号）
        function_body = source_code[body_start:body_end]
        
        # 生成POSIX兼容的函数定义
        # 无论原来是哪种形式，都转换为 func() { ... } 格式
        return f"{function_name}() {function_body}"