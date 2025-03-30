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
                # 查找函数的关键组件
                name_node = None
                body_node = None
                function_keyword = None
                
                for child in node.children:
                    if child.type == "word":  # 函数名
                        name_node = child
                    elif child.type == "compound_statement":  # 函数体
                        body_node = child
                    elif child.type == "function":  # function关键字
                        function_keyword = child
                
                if name_node and body_node:
                    # 确定函数声明结束位置（不包含函数体）
                    decl_end = body_node.start_byte
                    # 提取函数名
                    function_name = source_code[name_node.start_byte:name_node.end_byte]
                    # 生成POSIX兼容版本的函数声明
                    posix_decl = f"{function_name}() "
                    # 添加补丁，仅替换函数声明部分
                    patches.append((node.start_byte, decl_end, posix_decl))
                    
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
    