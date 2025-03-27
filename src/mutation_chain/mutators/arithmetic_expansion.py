from typing import Dict, Any, Tuple, Optional, List, Set
from src.mutation_chain import BaseMutator
import tree_sitter
import re

class ArithmeticExpansionMutator(BaseMutator):
    """将Bash中的算术扩展(ArithmeticExpansion)语法转换为POSIX兼容语法"""
    
    NAME = "arithmetic_expansion_mutator"
    DESCRIPTION = "将Bash算术扩展(ArithmeticExpansion)转换为POSIX兼容语法"
    TARGET_FEATURES = {"arithmetic_expansion"}
    
    # 定义所有与算术扩展相关的节点类型
    target_node_types = [
        "arithmetic_expansion",     # $(( ... ))
        "compound_statement",       # 独立的 (( ... )) 语句
    ]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash算术扩展语法转换为POSIX兼容代码
        
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
        
        # 遍历AST，收集所有目标节点
        def _traverse(node: tree_sitter.Node):
            if node.type in self.target_node_types:
                # 检查如果是compound_statement，确保它是算术扩展
                if node.type == "compound_statement":
                    # 判断是否为算术语句 (( ... ))
                    node_text = source_code[node.start_byte:node.end_byte]
                    if not node_text.strip().startswith('((') or not node_text.strip().endswith('))'):
                        for child in node.children:
                            _traverse(child)
                        return
                
                # 生成POSIX等效代码，并记录替换位置
                posix_code = self._generate_posix_code(node, source_code)
                if posix_code is not None:  # 只有生成了新代码才添加补丁
                    patches.append((node.start_byte, node.end_byte, posix_code))
            
            # 继续遍历子节点
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
        """根据具体节点生成POSIX代码"""
        node_text = source_code[node.start_byte:node.end_byte]
        
        # 是否为独立的算术语句 (( ... ))
        is_compound_statement = node.type == "compound_statement"
        
        # 提取算术表达式内容
        if is_compound_statement:
            # 从 (( ... )) 提取内部表达式
            match = re.match(r'\(\(\s*(.*?)\s*\)\)', node_text)
            if not match:
                return None  # 不是算术扩展
            expr = match.group(1)
        else:  # arithmetic_expansion: $(( ... ))
            # 从 $(( ... )) 提取内部表达式
            match = re.match(r'\$\(\(\s*(.*?)\s*\)\)', node_text)
            if not match:
                return None
            expr = match.group(1)
        
        # 处理独立的自增/自减操作: (( i++ )), (( i-- )), (( ++i )), (( --i ))
        inc_dec_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)(\+\+|\-\-)$', expr.strip())
        if inc_dec_match:
            var_name, operator = inc_dec_match.groups()
            operation = '+' if operator == '++' else '-'
            if is_compound_statement:
                return f"{var_name}=$(({var_name} {operation} 1))"
            else:
                return f"$(({var_name} {operation} 1))"
        
        pre_inc_dec_match = re.match(r'^(\+\+|\-\-)([a-zA-Z_][a-zA-Z0-9_]*)$', expr.strip())
        if pre_inc_dec_match:
            operator, var_name = pre_inc_dec_match.groups()
            operation = '+' if operator == '++' else '-'
            if is_compound_statement:
                return f"{var_name}=$(({var_name} {operation} 1))"
            else:
                return f"$(({var_name} {operation} 1))"
        
        # 处理幂运算 **: a ** b (转换为多个乘法，或使用 bc)
        if '**' in expr:
            # 首先用简单的正则表达式处理较简单的格式
            power_match = re.search(r'(\d+|\$[a-zA-Z_][a-zA-Z0-9_]*)\s*\*\*\s*(\d+)', expr)
            if power_match:
                base, exp = power_match.groups()
                try:
                    # 如果是数字指数，展开成多个乘法
                    exp_value = int(exp)
                    if exp_value <= 10:  # 限制展开大小
                        replacement = base
                        for i in range(exp_value - 1):
                            replacement += f" * {base}"
                        new_expr = expr[:power_match.start()] + replacement + expr[power_match.end():]
                        if is_compound_statement:
                            return f"(({new_expr}))"
                        else:
                            return f"$(({new_expr}))"
                except ValueError:
                    pass  # 不是简单的数字指数
        
        # 处理位移操作: << and >>
        if '<<' in expr or '>>' in expr:
            # 尝试替换位移操作符为乘法/除法表达式
            shift_left_match = re.search(r'(\d+|\$[a-zA-Z_][a-zA-Z0-9_]*)\s*<<\s*(\d+)', expr)
            if shift_left_match:
                base, shift = shift_left_match.groups()
                try:
                    shift_value = int(shift)
                    if shift_value <= 20:  # 限制展开大小
                        # 实现 "1 << 3" 为 "1 * 2 * 2 * 2" (2^3)
                        replacement = base
                        for i in range(shift_value):
                            replacement += " * 2"
                        new_expr = expr[:shift_left_match.start()] + replacement + expr[shift_left_match.end():]
                        if is_compound_statement:
                            return f"(({new_expr}))"
                        else:
                            return f"$(({new_expr}))"
                except ValueError:
                    pass
            
            shift_right_match = re.search(r'(\d+|\$[a-zA-Z_][a-zA-Z0-9_]*)\s*>>\s*(\d+)', expr)
            if shift_right_match:
                base, shift = shift_right_match.groups()
                try:
                    shift_value = int(shift)
                    if shift_value <= 20:  # 限制展开大小
                        # 实现 "8 >> 2" 为 "(8 / 2 / 2)" (除以2^2)
                        replacement = f"({base}"
                        for i in range(shift_value):
                            replacement += " / 2"
                        replacement += ")"
                        new_expr = expr[:shift_right_match.start()] + replacement + expr[shift_right_match.end():]
                        if is_compound_statement:
                            return f"(({new_expr}))"
                        else:
                            return f"$(({new_expr}))"
                except ValueError:
                    pass
        
        # 处理十六进制字面量: 0x10 -> 16#10
        def replace_hex_literal(match):
            hex_value = match.group(1)
            return f"16#{hex_value}"
        
        expr = re.sub(r'0x([0-9a-fA-F]+)', replace_hex_literal, expr)
        
        # 处理复合赋值操作符: +=, -=, *=, /=, %=, <<=, >>=, &=, ^=, |=
        compound_assign_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*(\+=|-=|\*=|/=|%=|<<=|>>=|&=|\^=|\|=)\s*(.*)', expr)
        if compound_assign_match:
            var_name, operator, value = compound_assign_match.groups()
            simple_op = operator[0]  # 提取基本操作符
            
            # 特殊处理移位操作符
            if operator == '<<=':
                try:
                    shift_value = int(value.strip())
                    if shift_value <= 20:  # 限制展开大小
                        replacement = f"{var_name} = {var_name}"
                        for i in range(shift_value):
                            replacement += " * 2"
                        if is_compound_statement:
                            return f"{var_name}=$(({replacement}))"
                        else:
                            return f"$(({replacement}))"
                except ValueError:
                    pass
            elif operator == '>>=':
                try:
                    shift_value = int(value.strip())
                    if shift_value <= 20:  # 限制展开大小
                        replacement = f"{var_name} = ({var_name}"
                        for i in range(shift_value):
                            replacement += " / 2"
                        replacement += ")"
                        if is_compound_statement:
                            return f"{var_name}=$(({replacement}))"
                        else:
                            return f"$(({replacement}))"
                except ValueError:
                    pass
            else:  # 处理其他复合赋值
                new_expr = f"{var_name} = {var_name} {simple_op} ({value})"
                if is_compound_statement:
                    return f"{var_name}=$(({new_expr}))"
                else:
                    return f"$(({new_expr}))"
        
        # 处理算术if条件: if (( a && b )) -> if [ "$a" -ne 0 ] && [ "$b" -ne 0 ]
        if is_compound_statement and self._is_condition_context(node, source_code):
            # 处理 && 逻辑与
            if '&&' in expr:
                parts = re.split(r'\s*&&\s*', expr)
                posix_parts = []
                
                for part in parts:
                    # 如果是变量或比较表达式
                    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', part.strip()):
                        # 单个变量检查非零
                        posix_parts.append(f'[ "${part.strip()}" -ne 0 ]')
                    else:
                        # 其他类型的表达式
                        posix_parts.append(f'[ "$(({part}))" -ne 0 ]')
                
                return " && ".join(posix_parts)
            
            # 处理 || 逻辑或
            elif '||' in expr:
                parts = re.split(r'\s*\|\|\s*', expr)
                posix_parts = []
                
                for part in parts:
                    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', part.strip()):
                        posix_parts.append(f'[ "${part.strip()}" -ne 0 ]')
                    else:
                        posix_parts.append(f'[ "$(({part}))" -ne 0 ]')
                
                return " || ".join(posix_parts)
            
            # 处理简单变量条件: if (( var )) -> if [ "$var" -ne 0 ]
            elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', expr.strip()):
                return f'[ "${expr.strip()}" -ne 0 ]'
            
            # 其他复杂条件表达式
            else:
                return f'[ "$(({expr}))" -ne 0 ]'
        
        # 默认情况：保持原始格式，但使用POSIX兼容语法
        if is_compound_statement:
            # 检查独立表达式是否是赋值
            assign_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)', expr)
            if assign_match:
                var_name, value = assign_match.groups()
                return f"{var_name}=$(({expr}))"
            else:
                return f"$(({expr}))"
        else:
            return f"$(({expr}))"
    
    def _is_condition_context(self, node: tree_sitter.Node, source_code: str) -> bool:
        """检查节点是否在条件语句（如if, while）的上下文中"""
        # 向上查找父节点
        current = node.parent
        while current:
            if current.type == "if_statement" or current.type == "while_statement":
                # 检查当前节点是否是条件部分
                for child in current.children:
                    if child.type == "condition" and node.start_byte >= child.start_byte and node.end_byte <= child.end_byte:
                        return True
            current = current.parent
        return False