from src.mutation_chain import BaseMutator, MutateResult
import tree_sitter
from typing import Dict, List

class ArrayMutator(BaseMutator):
    """将Bash数组语法转换为POSIX兼容代码"""
    
    def __init__(self):
        super().__init__()
        self.priority = 10  # 高优先级
    
    def can_transform(self, node: tree_sitter.Node, source_bytes: bytes, context: Dict) -> bool:
        # 检测数组声明
        if node.type == "variable_assignment":
            for child in node.children:
                if child.type == "array":
                    return True
        
        # 检测数组访问
        if node.type == "expansion":
            text = source_bytes[node.start_byte:node.end_byte].decode('utf8')
            return "[" in text and "]" in text
        
        return False
    
    def transform(self, node: tree_sitter.Node, source_bytes: bytes, 
                 context: Dict, children_results: Dict[int, MutateResult]) -> MutateResult:
        # 处理数组声明
        if node.type == "variable_assignment":
            return self._transform_array_declaration(node, source_bytes, context)
        
        # 处理数组访问
        if node.type == "expansion":
            return self._transform_array_access(node, source_bytes, context)
        
        # 默认返回未转换结果
        original_text = source_bytes[node.start_byte:node.end_byte].decode('utf8')
        return MutateResult(original_text, False)
    
    def _transform_array_declaration(self, node: tree_sitter.Node, source_bytes: bytes, context: Dict) -> MutateResult:
        """转换数组声明"""
        var_name = None
        array_node = None
        
        for child in node.children:
            if child.type == "variable_name":
                var_name = source_bytes[child.start_byte:child.end_byte].decode('utf8')
            elif child.type == "array":
                array_node = child
        
        if not var_name or not array_node:
            original_text = source_bytes[node.start_byte:node.end_byte].decode('utf8')
            return MutateResult(original_text, False)
        
        # 解析数组元素
        elements = []
        for child in array_node.children:
            # 跳过括号和空白
            if child.type in ["(", ")", "comment"]:
                continue
                
            # 提取元素文本
            element_text = source_bytes[child.start_byte:child.end_byte].decode('utf8').strip()
            if element_text:
                elements.append(element_text)
        
        # 生成POSIX兼容的变量声明
        result = []
        for i, element in enumerate(elements):
            result.append(f"{var_name}_{i}={element}")
        
        # 记录数组长度
        result.append(f"{var_name}_length={len(elements)}")
        
        # 更新数组信息到元数据
        metadata = {
            "arrays": {
                var_name: {
                    "length": len(elements),
                    "elements": elements
                }
            }
        }
        
        return MutateResult("\n".join(result), True, metadata)
    
    def _transform_array_access(self, node: tree_sitter.Node, source_bytes: bytes, context: Dict) -> MutateResult:
        """转换数组访问"""
        text = source_bytes[node.start_byte:node.end_byte].decode('utf8')
        
        # 使用正则可能更准确，但这里用一种简单方法处理常见情况
        import re
        array_access_pattern = re.compile(r'\${([a-zA-Z0-9_]+)\[([^]]+)\]}')
        
        def replace_array_access(match):
            array_name = match.group(1)
            index = match.group(2)
            
            if index.isdigit():
                return f"${{{array_name}_{index}}}"
            else:
                return f"$(eval echo \"\\${{{array_name}_$({index})}}\")"
        
        transformed_text = array_access_pattern.sub(replace_array_access, text)
        
        if transformed_text != text:
            return MutateResult(transformed_text, True)
        else:
            return MutateResult(text, False)