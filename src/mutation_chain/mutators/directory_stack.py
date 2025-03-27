from typing import Dict, Any, Optional, Tuple, List
from src.mutation_chain import BaseMutator
import tree_sitter
import re

class DirectoryStackMutator(BaseMutator):
    NAME = "directory_stack_mutator"
    DESCRIPTION = "将Bash DirectoryStack 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"DirectoryStack"}
    
    # Directory stack operations and tilde expansion with directory references
    target_node_types = ["command", "expansion"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash DirectoryStack 语法转换为POSIX兼容代码
        
        Args:
            source_code: 需要转换的源代码
            context: 可选的上下文信息，包含前序转换器的信息
            
        Returns:
            转换后的代码和更新后的上下文信息
        """
        context = context or {}
        patches = []
        needs_dirstack_functions = False
        
        # 解析AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # 遍历AST，收集所有目标节点
        def _traverse(node: tree_sitter.Node):
            nonlocal needs_dirstack_functions
            
            if node.type == "command":
                # 处理 pushd, popd, dirs 命令
                command_name_node = node.child_by_field_name("name")
                if command_name_node and command_name_node.text.decode('utf-8') in ["pushd", "popd", "dirs"]:
                    posix_code = self._transform_directory_command(node, source_code)
                    if posix_code:
                        patches.append((node.start_byte, node.end_byte, posix_code))
                        needs_dirstack_functions = True
                else:
                    # 处理命令参数中的目录栈引用
                    for child in node.children:
                        if child != command_name_node and child.type == "word":
                            word_text = source_code[child.start_byte:child.end_byte]
                            if re.search(r'^~[\+\-]\d+$', word_text):
                                posix_code = self._transform_dirstack_expansion(child, source_code)
                                if posix_code:
                                    patches.append((child.start_byte, child.end_byte, posix_code))
                        needs_dirstack_functions = True
            
            elif node.type == "expansion":
                # 处理目录栈引用，如 ~+3 或 ~-2
                text = source_code[node.start_byte:node.end_byte]
                if re.search(r'~[\+\-]\d+', text):
                    posix_code = self._transform_dirstack_expansion(node, source_code)
                    if posix_code:
                        patches.append((node.start_byte, node.end_byte, posix_code))
                        needs_dirstack_functions = True
            
            for child in node.children:
                _traverse(child)
        
        # 执行遍历
        if root:
            _traverse(root)
        
        # 添加目录栈相关的函数定义和初始化
        if needs_dirstack_functions and patches:
            dirstack_functions = self._get_dirstack_functions()
            patches.append((0, 0, dirstack_functions))
        
        # 更新上下文信息
        transformed_features = context.get('transformed_features', set())
        transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        # 应用补丁并返回结果
        return self.apply_patches(source_code, patches), context
    
    def _transform_directory_command(self, node: tree_sitter.Node, source_code: str) -> str:
        """转换目录栈相关命令（pushd, popd, dirs）"""
        command_name_node = node.child_by_field_name("name")
        command_name = command_name_node.text.decode('utf-8') if command_name_node else ""
        
        if command_name == "pushd":
            # 获取参数
            arguments = []
            for child in node.children:
                # 跳过命令名节点，只处理参数
                if child != command_name_node and child.type != "comment":
                    arg_text = source_code[child.start_byte:child.end_byte]
                    arguments.append(arg_text)
            
            if arguments:
                return f"dirstack_push {' '.join(arguments)}"
            else:
                return "dirstack_push ."  # Default behavior for pushd without arguments
                
        elif command_name == "popd":
            return "dirstack_pop"
            
        elif command_name == "dirs":
            return 'printf "%s\\n" "$DIRSTACK" | tr ":" "\\n"'
        
        return ""
    
    def _transform_dirstack_expansion(self, node: tree_sitter.Node, source_code: str) -> str:
        """转换目录栈引用表达式（~+N 或 ~-N）"""
        text = source_code[node.start_byte:node.end_byte]

        # 匹配 ~+N 或 ~-N 模式
        match = re.search(r'~([\+\-])(\d+)', text)
        if match:
            sign, index = match.groups()
            if sign == '+':
                return f'"$(dirstack_get {index})"'
            else:  # sign == '-'
                return f'"$(dirstack_get -{index})"'
        
        return ""
    
    def _get_dirstack_functions(self) -> str:
        """返回POSIX shell的目录栈函数定义"""
        return """
DIRSTACK="$PWD"

dirstack_push() {
  target_dir="$1"
  cd "$target_dir" || return 1
  DIRSTACK="$PWD:${DIRSTACK}" 
}

dirstack_pop() {
  top_dir="${DIRSTACK%%:*}"
  remaining_stack="${DIRSTACK#*:}"
  if [ "$remaining_stack" = "$DIRSTACK" ]; then
    echo "Error: Directory stack empty." >&2
    return 1
  fi
  cd "$top_dir" || return 1
  DIRSTACK="$remaining_stack"
}

dirstack_get() {
  index=$1
  dirstack_file=$(mktemp "/tmp/dirstack.XXXXXX")
  
  echo "$DIRSTACK" | tr ':' '\\n' > "$dirstack_file"
  if [ "$index" -lt 0 ]; then
    total=$(wc -l < "$dirstack_file")
    index=$((total + index))
  fi
  awk "NR == $index" "$dirstack_file"
  rm "$dirstack_file"
}

"""