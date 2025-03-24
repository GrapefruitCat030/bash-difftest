from typing import Dict, Any, Optional, Tuple, List
import tree_sitter
from src.mutation_chain import BaseMutator

class RedirectionsMutator(BaseMutator):
    NAME = "redirection_mutator"
    DESCRIPTION = "将Bash Redirections 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"redirections"}
    
    # 主要目标是redirected_statement节点
    target_node_types = ["redirected_statement"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash Redirections 语法转换为POSIX兼容代码
        
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
        
        # 遍历AST，查找所有redirected_statement节点
        def _traverse(node: tree_sitter.Node):
            if node.type in self.target_node_types:
                self._process_redirection(node, source_code, patches)
            
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
    
    def _process_redirection(self, node: tree_sitter.Node, source_code: str, patches: List) -> None:
        """
        处理redirected_statement节点
        """
        # 查找file_redirect子节点
        file_redirect_node = None
        for child in node.children:
            if child.type == "redirect" or child.type == "file_redirect":
                file_redirect_node = child
                break
        
        if not file_redirect_node:
            # 如果没有找到file_redirect，可能在更深层次
            for child in node.children:
                if child.type == "redirect":
                    for grandchild in child.children:
                        if grandchild.type == "file_redirect":
                            file_redirect_node = grandchild
                            break
                    if file_redirect_node:
                        break
        
        # 没有找到file_redirect节点，返回
        if not file_redirect_node:
            return
        
        # 查找重定向操作符和目标文件
        operator_node = None
        destination_node = None
        
        for child in file_redirect_node.children:
            # 查找操作符 - 在AST中是直接的文本节点 "&>" 或 "&>>"
            if not operator_node and (source_code[child.start_byte:child.end_byte] == "&>" or 
                                     source_code[child.start_byte:child.end_byte] == "&>>"):
                operator_node = child
            
            # 查找目标文件 - destination或word节点
            if child.type == "destination" or child.type == "word":
                destination_node = child
        
        # 如果找到了操作符和目标文件
        if operator_node and destination_node:
            op_text = source_code[operator_node.start_byte:operator_node.end_byte]
            file_text = source_code[destination_node.start_byte:destination_node.end_byte]
            
            # 构建POSIX兼容的重定向
            if op_text == "&>":
                posix_redirect = f">{file_text} 2>&1"
            elif op_text == "&>>":
                posix_redirect = f">>{file_text} 2>&1"
            else:
                return  # 不是目标操作符，跳过
            
            # 创建补丁，替换整个重定向操作符和目标文件部分
            start = operator_node.start_byte
            end = destination_node.end_byte
            patches.append((start, end, posix_redirect))