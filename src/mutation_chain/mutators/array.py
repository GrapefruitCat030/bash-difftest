from src.mutation_chain import BaseMutator
import tree_sitter
from typing import Any, Dict, Optional, Tuple, List

class ArrayMutator(BaseMutator):
    # 定义转换器基本信息
    NAME = "array_mutator"
    DESCRIPTION = "将Bash Array 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"Array"}
    
    # 目标节点类型：数组声明、数组操作、数组引用等
    target_node_types = [
        "array",             # 数组声明 arr=("a" "b" "c")
        "subscript",         # 数组下标访问 ${arr[1]}
        "expansion",         # 数组扩展 ${arr[@]} ${#arr[@]} ${!arr[@]} ${arr[@]:1:2}
        "variable_assignment"  # 数组元素赋值 arr[2]="d" 或 arr+=("d")
    ]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash Array 语法转换为POSIX兼容代码
        
        Args:
            source_code: 需要转换的源代码
            context: 可选的上下文信息，包含前序转换器的信息
            
        Returns:
            转换后的代码和更新后的上下文信息
        """
        # 初始化上下文（如果没有提供）
        context = context or {}
        context['arrays'] = context.get('arrays', {})
        patches = []
        
        # 解析AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # 首先识别所有数组声明
        self._identify_arrays(root, source_code, context)

        # 遍历AST处理所有目标节点
        def _traverse(node: tree_sitter.Node):
            # 先处理节点自身
            if node.type in self.target_node_types:
                patch = self._process_node(node, source_code, context)
                if patch:
                    patches.extend(patch)
            
            # 再递归处理子节点
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
    
    def _identify_arrays(self, root_node: tree_sitter.Node, source_code: str, context: Dict[str, Any]):
        """识别代码中的数组声明，并记录到上下文中"""
        def _traverse(node):
            if node.type == "variable_assignment":
                # 检查是否为数组声明
                for child in node.children:
                    if child.type == "array":
                        # 获取数组名称
                        name_node = node.child_by_field_name("name")
                        if name_node:
                            array_name = source_code[name_node.start_byte:name_node.end_byte]
                            context['arrays'][array_name] = {'is_array': True, 'length': 0}
                
                # 检查是否为下标赋值形式：arr[0]="value"
                name_node = node.child_by_field_name("name")
                if name_node and name_node.type == "subscript":
                    # 获取数组名
                    array_name_node = name_node.child_by_field_name("name")
                    if array_name_node:
                        array_name = source_code[array_name_node.start_byte:array_name_node.end_byte]
                        # 如果数组不存在，则添加到上下文
                        if array_name not in context['arrays']:
                            context['arrays'][array_name] = {'is_array': True, 'length': 0}

            # 递归处理子节点
            for child in node.children:
                _traverse(child)
        
        _traverse(root_node)
    
    def _process_node(self, node: tree_sitter.Node, source_code: str, context: Dict[str, Any]) -> List[Tuple[int, int, str]]:
        """根据节点类型处理不同的数组操作"""
        patches = []
        
        if node.type == "array":
            # 处理数组声明: arr=("a" "b" "c")
            parent = node.parent
            if parent and parent.type == "variable_assignment" and parent.children[1].type == "=":
                patches.extend(self._handle_array_declaration(parent, source_code, context))
        
        elif node.type == "subscript":
            # 检查父节点是否为expansion
            parent = node.parent
            if parent and parent.type == "expansion":
                # 处理数组下标访问: ${arr[1]}
                patches.extend(self._handle_array_subscript(parent, source_code, context))
            
        elif node.type == "expansion":
            # 检查是否为数组扩展（长度或遍历）
            text = source_code[node.start_byte:node.end_byte]
            if "@" in text or "*" in text:
                # 处理数组扩展: ${arr[@]} 或 ${#arr[@]}
                patches.extend(self._handle_array_expansion(node, source_code, context))
        
        elif node.type == "variable_assignment":
            # 检查是否为数组元素赋值或数组追加
            name_node = node.child_by_field_name("name")
            if name_node and name_node.type == "subscript":
                # 处理数组元素赋值: arr[2]="d"
                patches.extend(self._handle_array_element_assignment(node, source_code, context))
            else:
                # 检查是否为数组追加: arr+=("d")
                text = source_code[node.start_byte:node.end_byte]
                if "+=" in text and "(" in text and ")" in text:
                    # 处理数组追加操作
                    patches.extend(self._handle_array_append(node, source_code, context))

        return patches
    
    def _handle_array_declaration(self, node: tree_sitter.Node, source_code: str, context: Dict[str, Any]) -> List[Tuple[int, int, str]]:
        """处理数组声明 arr=("a" "b" "c")"""

        # 获取数组名称
        name_node = node.child_by_field_name("name")
        if not name_node:
            return []
        
        array_name = source_code[name_node.start_byte:name_node.end_byte]
        
        # 获取数组元素
        array_node = None
        for child in node.children:
            if child.type == "array":
                array_node = child
                break
        
        if not array_node:
            return []
        
        # 解析数组元素
        elements = []
        for child in array_node.children:
            if child.type != "(" and child.type != ")":
                elements.append(source_code[child.start_byte:child.end_byte])

        # 生成POSIX兼容代码
        posix_code = []
        for i, element in enumerate(elements):
            posix_code.append(f"{array_name}_{i}={element};")
        
        posix_code.append(f"{array_name}__len={len(elements)}")
        
        # 记录数组信息到上下文
        context['arrays'][array_name] = {
            'is_array': True,
            'length': len(elements),
            'elements': elements
        }
        
        return [(node.start_byte, node.end_byte, " ".join(posix_code))]
    
    def _handle_array_subscript(self, node: tree_sitter.Node, source_code: str, context: Dict[str, Any]) -> List[Tuple[int, int, str]]:
        """处理数组下标访问 ${arr[1]}"""
        # 找到subscript节点
        subscript_node = None
        operator = None
        
        for child in node.children:
            if child.type == "operator":
                operator = source_code[child.start_byte:child.end_byte]
            elif child.type == "subscript":
                subscript_node = child
        
        if not subscript_node:
            return []
        
        # 获取数组名称
        name_node = subscript_node.child_by_field_name("name")
        if not name_node:
            return []
        
        array_name = source_code[name_node.start_byte:name_node.end_byte]
        
        # 获取索引
        index_node = subscript_node.child_by_field_name("index")
        if not index_node:
            return []
        
        index_text = source_code[index_node.start_byte:index_node.end_byte]
        
        # # 检查是否为已知数组
        # if array_name not in context['arrays']:
        #     return []
        
        # 处理数字索引
        if index_node.type == "number":
            # 直接访问指定索引
            posix_code = f"${array_name}_{index_text}"
            return [(node.start_byte, node.end_byte, posix_code)]
        
        return []
    
    def _handle_array_expansion(self, node: tree_sitter.Node, source_code: str, context: Dict[str, Any]) -> List[Tuple[int, int, str]]:
        """处理数组扩展 ${arr[@]}, ${#arr[@]}"""
        text = source_code[node.start_byte:node.end_byte]
        
        # 查找操作符和subscript节点
        operator = None
        subscript_node = None
        for child in node.children:
            if child.type == "#":
                operator = "#"
            elif child.type == "subscript":
                subscript_node = child
        
        if not subscript_node:
            return []
        
        # 获取数组名称
        name_node = subscript_node.child_by_field_name("name")
        if not name_node:
            return []
        
        array_name = source_code[name_node.start_byte:name_node.end_byte]
        
        # 获取索引
        index_node = subscript_node.child_by_field_name("index")
        if not index_node:
            return []
        
        index_text = source_code[index_node.start_byte:index_node.end_byte]

        # 检查是否为已知数组 (保留此检查，因为需要知道数组长度)
        if array_name not in context['arrays']:
            # 如果是数组长度查询但数组未知，默认返回0
            if operator == "#" and index_text == "@":
                return [(node.start_byte, node.end_byte, "\"0\"")]
            return []
        
        # 处理数组长度 ${#arr[@]}
        if operator == "#" and index_text == "@":
            return [(node.start_byte, node.end_byte, f"${array_name}__len")]
        
        # 处理完整数组展开 ${arr[@]}
        if index_text == "@":
            # 构建所有元素的展开
            elements = []
            array_len = context['arrays'][array_name].get('length', 0)
            
            for i in range(array_len):
                elements.append(f"${array_name}_{i}")
            
            if elements:
                return [(node.start_byte, node.end_byte, " ".join(elements))]
        
        return []
    
    def _handle_array_element_assignment(self, node: tree_sitter.Node, source_code: str, context: Dict[str, Any]) -> List[Tuple[int, int, str]]:
        """处理数组元素赋值 arr[2]="d" """
        # 获取数组名和索引
        name_node = node.child_by_field_name("name")
        if not name_node or name_node.type != "subscript":
            return []
        
        # 获取数组名
        array_name_node = name_node.child_by_field_name("name")
        if not array_name_node:
            return []
        
        array_name = source_code[array_name_node.start_byte:array_name_node.end_byte]
        
        # 获取索引
        index_node = name_node.child_by_field_name("index")
        if not index_node:
            return []
        
        index_text = source_code[index_node.start_byte:index_node.end_byte]
        
        # 获取赋值表达式
        value_node = node.child_by_field_name("value")
        if not value_node:
            return []
        
        value_text = source_code[value_node.start_byte:value_node.end_byte]
        
        # 如果数组不存在于上下文中，则添加
        if array_name not in context['arrays']:
            context['arrays'][array_name] = {'is_array': True, 'length': 0}
        
        # 处理常量索引
        if index_node.type == "number":
            posix_index = int(index_text)
            posix_code = f"{array_name}_{posix_index}={value_text}"
            
            # 如果需要更新数组长度
            update_len = ""
            if posix_index >= context['arrays'][array_name].get('length', 0):
                update_len = f"; {array_name}__len=$(({posix_index} + 1))"
                # 更新上下文中的长度
                context['arrays'][array_name]['length'] = posix_index + 1
            
            return [(node.start_byte, node.end_byte, f"{posix_code}{update_len}")]
        
        return []
    
    def _handle_array_append(self, node: tree_sitter.Node, source_code: str, context: Dict[str, Any]) -> List[Tuple[int, int, str]]:
        """处理数组追加 arr+=("d")"""

        text = source_code[node.start_byte:node.end_byte]
        
        # 检查是否为数组+=操作
        if "+=" not in text or "(" not in text or ")" not in text:
            return []
        
        # 获取数组名称
        name_node = node.child_by_field_name("name")
        if not name_node:
            return []
        
        array_name = source_code[name_node.start_byte:name_node.end_byte]
        
        # 如果数组不存在于上下文中，则添加
        if array_name not in context['arrays']:
            context['arrays'][array_name] = {'is_array': True, 'length': 0}
        
        # 获取数组值
        value_node = node.child_by_field_name("value")
        if not value_node or value_node.type != "array":
            return []
        
        # 解析要追加的元素
        elements = []
        for child in value_node.children:
            if child.type == "string":
                elements.append(source_code[child.start_byte:child.end_byte])
        
        if not elements:
            return []
        
        # 生成追加元素的代码
        posix_code_lines = []
        current_len = context['arrays'][array_name].get('length', 0)
        
        for i, element in enumerate(elements):
            new_index = current_len + i
            posix_code_lines.append(f"{array_name}_{new_index}={element}")
        
        posix_code_lines.append(f"{array_name}__len=$(({current_len} + {len(elements)}))")
        
        # 更新上下文中的长度
        context['arrays'][array_name]['length'] = current_len + len(elements)
        
        return [(node.start_byte, node.end_byte, "; ".join(posix_code_lines))]

