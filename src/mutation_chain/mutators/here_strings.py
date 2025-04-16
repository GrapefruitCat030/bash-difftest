from typing import Dict, Any, Tuple, Optional, List
import tree_sitter
from src.mutation_chain import BaseMutator

class HereStringsMutator(BaseMutator):
    NAME = "here_string_mutator"
    DESCRIPTION = "将Bash HereString 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"herestring"}
    
    # 正确的节点类型应该是"herestring_redirect"而不是"here_string"
    target_node_types = ["herestring_redirect"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash HereString 语法转换为POSIX兼容代码
        
        Args:
            source_code: 需要转换的源代码
            context: 可选的上下文信息，包含前序转换器的信息
            
        Returns:
            转换后的代码和更新后的上下文信息
        """
        # 初始化上下文（如果没有提供）
        context = context or {}
        patches = []
        
        # 解析AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # 遍历AST，收集所有herestring_redirect节点
        self._traverse(root, source_code, patches)
        
        # 更新上下文信息
        transformed_features = context.get('transformed_features', set())
        transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        # 应用补丁并返回结果
        return self.apply_patches(source_code, patches), context
    
    def _traverse(self, node: tree_sitter.Node, source_code: str, patches: list):
        """遍历AST找到目标节点并处理"""
        if node.type in self.target_node_types:
            self._process_herestring(node, source_code, patches)
        
        for child in node.children:
            self._traverse(child, source_code, patches)
    
    def _process_herestring(self, node: tree_sitter.Node, source_code: str, patches: list):
        """处理herestring_redirect节点"""
        # 找到包含herestring的父节点
        parent = node.parent
        
        # 获取字符串内容
        string_content = None
        for child in node.children:
            if child.type == "string" or child.type == "raw_string":
                string_content = source_code[child.start_byte:child.end_byte]
                break
        
        if string_content is None:
            return
        
        # 确定命令上下文
        command_context = self._determine_command_context(parent)
        if not command_context:
            return
        
        command_node, cmd_start, cmd_parts, redirects, is_pipeline = command_context
        
        # 构建替换代码
        replacement = self._build_replacement(command_node, cmd_parts, string_content, redirects, is_pipeline, source_code)

        # 添加补丁
        patches.append((command_node.start_byte, command_node.end_byte, replacement))
    
    def _determine_command_context(self, node: tree_sitter.Node):
        """确定包含herestring的命令上下文"""
        # 直接命令节点
        if node.type == "command":
            cmd_parts = []
            redirects = []
            is_pipeline = False
            
            # 检查父节点是否是管道
            if node.parent and node.parent.type == "pipeline":
                is_pipeline = True
            
            # 收集命令部分和重定向部分
            for child in node.children:
                if child.type == "command_name" or child.type == "word" or child.type == "string":
                    cmd_parts.append((child.start_byte, child.end_byte))
                elif "redirect" in child.type and child.type != "herestring_redirect":
                    redirects.append((child.start_byte, child.end_byte))
            
            return node, node.start_byte, cmd_parts, redirects, is_pipeline
        
        # 重定向语句
        elif node.type == "redirected_statement":
            cmd_parts = []
            redirects = []
            is_pipeline = False
            
            # 检查父节点是否是管道
            if node.parent and node.parent.type == "pipeline":
                is_pipeline = True
            
            # 找到命令体
            command_node = None
            for child in node.children:
                if child.type == "command":
                    command_node = child
                    # 收集命令部分
                    for cmd_child in child.children:
                        if cmd_child.type == "command_name" or cmd_child.type == "word" or cmd_child.type == "string":
                            cmd_parts.append((cmd_child.start_byte, cmd_child.end_byte))
                elif "redirect" in child.type and child.type != "herestring_redirect":
                    redirects.append((child.start_byte, child.end_byte))
            
            return node, node.start_byte, cmd_parts, redirects, is_pipeline
        
        # 管道中的命令
        elif node.type == "pipeline":
            # 在管道中找到包含herestring的命令
            for child in node.children:
                if child.type == "command":
                    for cmd_child in child.children:
                        if cmd_child.type == "herestring_redirect":
                            cmd_parts = []
                            redirects = []
                            
                            # 收集命令部分
                            for part in child.children:
                                if part.type == "command_name" or part.type == "word" or part.type == "string":
                                    cmd_parts.append((part.start_byte, part.end_byte))
                                elif "redirect" in part.type and part.type != "herestring_redirect":
                                    redirects.append((part.start_byte, part.end_byte))
                            
                            return node, node.start_byte, cmd_parts, redirects, True
        
        return None
    
    def _build_replacement(self, command_node, cmd_parts, string_content, redirects, is_pipeline, source_code):
        """构建替换代码"""
        # 构建命令部分
        cmd_text = " ".join([source_code[start:end] for start, end in cmd_parts])
        
        # 构建重定向部分
        redirect_text = " ".join([source_code[start:end] for start, end in redirects])

        # 构建基本替换
        replacement = f'printf "%s\\n" {string_content} | {cmd_text}'
        
        # 添加重定向
        if redirect_text:
            replacement += f" {redirect_text}"
        
        # 处理管道情况
        if is_pipeline:
            # 获取原代码
            original_code = source_code[command_node.start_byte:command_node.end_byte]
            
            # 如果是管道的第一个命令
            if command_node.type == "pipeline":
                # 找到第一个管道符号后的内容
                pipe_parts = original_code.split("|", 1)
                if len(pipe_parts) > 1:
                    # 第一个命令已经转换为printf | cmd，所以我们只需要添加后面的管道部分
                    replacement += f" | {pipe_parts[1].strip()}"
        
        return replacement
