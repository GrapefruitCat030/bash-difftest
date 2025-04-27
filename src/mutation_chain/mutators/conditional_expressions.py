from typing import Dict, Any, Tuple, Optional, List
from src.mutation_chain import BaseMutator
import tree_sitter
import re

class ConditionalExpressionsMutator(BaseMutator):
    NAME = "conditional_expression_mutator"
    DESCRIPTION = "将Bash条件表达式 [[ ]] 转换为POSIX兼容语法 [ ]"
    TARGET_FEATURES = {"ConditionalExpressions"}
    
    # 在tree-sitter-bash中，[[...]] 表达式被解析为test_command节点
    target_node_types = ["test_command"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash条件表达式语法转换为POSIX兼容代码
        
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
        
        # 遍历AST，找到所有的 [[ ]] 条件表达式
        def _traverse(node: tree_sitter.Node):
            if node.type in self.target_node_types:
                node_text = source_code[node.start_byte:node.end_byte].strip()
                if node_text.startswith("[[") and node_text.endswith("]]"):
                    posix_code = self._convert_to_posix(node, source_code)
                    patches.append((node.start_byte, node.end_byte, posix_code))
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
    
    def _convert_to_posix(self, node: tree_sitter.Node, source_code: str) -> str:
        """将单个 [[ ]] 条件表达式转换为POSIX语法"""
        expr_text = source_code[node.start_byte:node.end_byte]
        inner_expr = expr_text[2:-2].strip()  # 去掉 [[ 和 ]]

        # 检查是否包含regex匹配 (=~)
        for child in node.children:
            if child.type == "binary_expression" and "=~" in source_code[child.start_byte:child.end_byte]:
                return self._convert_regex_match_from_node(child, source_code)
        
        # 处理括号分组和逻辑操作符的复杂表达式
        if ("(" in inner_expr and ")" in inner_expr) or " && " in inner_expr or " || " in inner_expr:
            return self._convert_complex_expression(inner_expr)
        
        # 处理简单条件表达式
        return self._convert_simple_condition(inner_expr)
    
    def _convert_regex_match_from_node(self, node: tree_sitter.Node, source_code: str) -> str:
        """
        根据AST节点转换正则表达式匹配
        修改: 增加了对带否定操作符(!)的正则表达式处理
        """
        # 检查是否有否定操作符
        has_negation = False
        left_expr = ""
        pattern = ""
        
        # 检查左侧是否为一元表达式(带!)
        if node.child_by_field_name("left").type == "unary_expression":
            has_negation = True
            unary_node = node.child_by_field_name("left")
            # 获取!后面的实际表达式
            if unary_node.child_count > 1:  # 确保有足够的子节点
                expr_node = unary_node.children[1]  # !后面的表达式
                left_expr = source_code[expr_node.start_byte:expr_node.end_byte]
        else:
            left_expr = source_code[node.child_by_field_name("left").start_byte:node.child_by_field_name("left").end_byte]
        
        # 获取右侧的正则表达式
        right_node = node.child_by_field_name("right")
        if right_node:
            pattern = source_code[right_node.start_byte:right_node.end_byte]
        
        # 确保变量引用有引号
        quoted_left = self._ensure_quoted(left_expr)
        
        # 构建POSIX兼容的grep命令
        grep_cmd = f"echo {quoted_left} | grep -Eq \"{pattern}\""
        
        # 如果有否定操作符，添加否定
        if has_negation:
            return f"(! {grep_cmd})"
        else:
            return f"({grep_cmd})"
    
    def _convert_complex_expression(self, expr: str) -> str:
        """转换包含逻辑操作符或分组的复杂表达式"""
        # 处理带括号的分组
        if "(" in expr and ")" in expr:
            # 简单处理：替换外部逻辑操作符
            if " && " in expr:
                parts = self._split_considering_brackets(expr, "&&")
                converted_parts = []
                for part in parts:
                    part = part.strip()
                    if part.startswith("(") and part.endswith(")"):
                        # 递归处理括号内容
                        inner = part[1:-1].strip()
                        inner_converted = self._convert_complex_expression(inner)
                        # 处理括号内的表达式结果
                        if inner_converted.startswith("[") and inner_converted.endswith("]"):
                            converted_parts.append(inner_converted)
                        else:
                            converted_parts.append(f"( {inner_converted} )")
                    else:
                        # 直接处理简单条件
                        converted_parts.append(f"[ {self._convert_condition_parts(part)} ]")
                return " && ".join(converted_parts)
            elif " || " in expr:
                parts = self._split_considering_brackets(expr, "||")
                converted_parts = []
                for part in parts:
                    part = part.strip()
                    if part.startswith("(") and part.endswith(")"):
                        inner = part[1:-1].strip()
                        inner_converted = self._convert_complex_expression(inner)
                        if inner_converted.startswith("[") and inner_converted.endswith("]"):
                            converted_parts.append(inner_converted)
                        else:
                            converted_parts.append(f"( {inner_converted} )")
                    else:
                        converted_parts.append(f"[ {self._convert_condition_parts(part)} ]")
                return " || ".join(converted_parts)
        
        # 处理简单的逻辑操作符
        if " && " in expr:
            parts = expr.split(" && ")
            converted_parts = [self._convert_condition_parts(part.strip()) for part in parts]
            return "[ " + " ] && [ ".join(converted_parts) + " ]"
        
        if " || " in expr:
            parts = expr.split(" || ")
            converted_parts = [self._convert_condition_parts(part.strip()) for part in parts]
            return "[ " + " ] || [ ".join(converted_parts) + " ]"
        
        # 如果没有识别出复杂结构，返回简单处理结果
        return self._convert_simple_condition(expr)
    
    def _split_considering_brackets(self, expr: str, delimiter: str) -> List[str]:
        """考虑括号嵌套的情况下分割表达式"""
        result = []
        current = ""
        depth = 0
        
        i = 0
        while i < len(expr):
            if expr[i] == '(':
                depth += 1
                current += expr[i]
            elif expr[i] == ')':
                depth -= 1
                current += expr[i]
            elif expr[i:i+len(delimiter)] == delimiter and depth == 0:
                result.append(current.strip())
                current = ""
                i += len(delimiter) - 1  # 跳过分隔符其余部分
            else:
                current += expr[i]
            i += 1
        
        if current:
            result.append(current.strip())
        
        return result
    
    def _convert_simple_condition(self, expr: str) -> str:
        """转换简单条件表达式"""
        return f"[ {self._convert_condition_parts(expr)} ]"
    
    def _convert_condition_parts(self, expr: str) -> str:
        """转换条件表达式的各个部分"""
        expr = expr.strip()
        
        # 处理变量存在检查 -v 语法
        if expr.startswith("-v "):
            var = expr[3:].strip()
            # 移除可能的 $ 符号
            if var.startswith("$"):
                var = var[1:]
            return f"-n \"${{{var}+x}}\""
        
        # 处理 == 比较 (在POSIX中用 = 替代)
        if " == " in expr:
            left, right = expr.split(" == ", 1)
            return f"{self._ensure_quoted(left.strip())} = {self._ensure_quoted(right.strip())}"
        
        # 处理 != 比较
        if " != " in expr:
            left, right = expr.split(" != ", 1)
            return f"{self._ensure_quoted(left.strip())} != {self._ensure_quoted(right.strip())}"
        
        # 处理 < 比较 (在POSIX中需要转义)
        if " < " in expr:
            left, right = expr.split(" < ", 1)
            return f"{self._ensure_quoted(left.strip())} \\< {self._ensure_quoted(right.strip())}"
        
        # 处理 > 比较 (在POSIX中需要转义)
        if " > " in expr:
            left, right = expr.split(" > ", 1)
            return f"{self._ensure_quoted(left.strip())} \\> {self._ensure_quoted(right.strip())}"
        
        # 处理 -n 非空检查
        if expr.startswith("-n "):
            var = expr[3:].strip()
            return f"-n {self._ensure_quoted(var)}"
        
        # 处理 ! -z 变量非空检查 (等价于 -n)
        if expr.startswith("! -z "):
            var = expr[5:].strip()
            return f"-n {self._ensure_quoted(var)}"
        
        # 处理其他条件，确保变量引用都有引号
        return self._add_quotes_to_vars(expr)
    
    def _ensure_quoted(self, expr: str) -> str:
        """确保变量表达式有引号"""
        expr = expr.strip()
        
        # 如果表达式已经被引号包围，则返回原样
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr
        
        # 如果是变量引用，添加双引号
        if expr.startswith("$"):
            return f"\"{expr}\""
        
        # 变量为空值的安全处理
        if expr == "":
            return "\"\""
            
        # 如果是模式匹配或其他特殊语法，保留原样
        if "*" in expr or "?" in expr:
            return expr
            
        # 其他情况，如果含有空格，添加引号
        if " " in expr:
            return f"\"{expr}\""
        
        return expr
    
    def _add_quotes_to_vars(self, expr: str) -> str:
        """在表达式中给所有变量添加引号"""
        # 匹配变量模式：$var 或 ${var}
        var_pattern = r'(\$\w+|\$\{[^}]+\})'
        
        def quote_var(match):
            var = match.group(1)
            return f"\"{var}\""
        
        # 替换所有变量为带引号的形式
        return re.sub(var_pattern, quote_var, expr)