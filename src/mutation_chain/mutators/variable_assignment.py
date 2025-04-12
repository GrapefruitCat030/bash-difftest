import re
from typing import Any, Dict, Optional, Tuple, Set
import tree_sitter
from src.mutation_chain import BaseMutator

class VariableAssignmentMutator(BaseMutator):
    # Define transformer basic information
    NAME = "variable_assignment_mutator"
    DESCRIPTION = "将Bash += 变量赋值和 declare -i 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"variable_assignment_append"}
    
    # Added declaration_command to target node types to handle declare -i
    target_node_types = ["variable_assignment", "declaration_command"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash += 变量赋值语法及 declare -i 转换为POSIX兼容代码
        
        Args:
            source_code: 需要转换的源代码
            context: 可选的上下文信息，包含前序转换器的信息
            
        Returns:
            转换后的代码和更新后的上下文信息
        """
        # Initialize context if not provided
        context = context or {}
        # Track integer variables
        integer_vars = self._find_integer_variables(source_code)
        
        patches = []
        
        # Parse AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # Traverse AST and collect all target nodes
        def _traverse(node: tree_sitter.Node):
            if node.type in self.target_node_types:
                if node.type == "variable_assignment" and self._is_append_operator(node, source_code):
                    # Handle += operator assignment
                    posix_code = self._generate_posix_code(node, source_code, integer_vars)
                    patches.append((node.start_byte, node.end_byte, posix_code))
                elif node.type == "declaration_command" and self._is_declare_i(node, source_code):
                    # Handle declare -i command
                    posix_code = self._transform_declare_i(node, source_code)
                    patches.append((node.start_byte, node.end_byte, posix_code))
            for child in node.children:
                _traverse(child)
        
        # Execute traversal
        if root:
            _traverse(root)
        
        # Update context information
        transformed_features = context.get('transformed_features', set())
        transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        # Apply patches and return result
        return self.apply_patches(source_code, patches), context
    
    def _find_integer_variables(self, source_code: str) -> Set[str]:
        """
        Find all variables declared as integers using declare -i
        """
        integer_vars = set()
        # Find all declare -i statements and extract variable names
        declare_pattern = r'declare\s+-i\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(declare_pattern, source_code):
            integer_vars.add(match.group(1))
        
        return integer_vars
    
    def _is_append_operator(self, node: tree_sitter.Node, source_code: str) -> bool:
        """
        Check if the node represents a += operation
        According to the AST, += is a direct property of the variable_assignment node
        """
        # Looking for the += operator directly in the children
        for child in node.children:
            # In the tree-sitter-bash AST, the operator is a direct child text node
            if child.type == '+=':
                return True
        return False
    
    def _is_declare_i(self, node: tree_sitter.Node, source_code: str) -> bool:
        """
        Check if the node represents a declare -i command
        """
        if len(node.children) < 3:
            return False
        
        # Check if the first child is 'declare'
        if node.children[0].type != 'declare':
            return False
            
        # Check if there's a -i flag
        for i in range(1, len(node.children)):
            if node.children[i].type == 'word':
                word_text = source_code[node.children[i].start_byte:node.children[i].end_byte]
                if word_text == '-i':
                    return True
                
        return False
    
    def _transform_declare_i(self, node: tree_sitter.Node, source_code: str) -> str:
        """
        Transform 'declare -i var=value' to 'var=value'
        """
        # Extract the variable assignment part
        for child in node.children:
            if child.type == 'variable_assignment':
                var_name = None
                var_value = None
                
                for assignment_child in child.children:
                    if assignment_child.type == 'variable_name':
                        var_name = source_code[assignment_child.start_byte:assignment_child.end_byte]
                    elif assignment_child.type == '=':
                        continue
                    else:
                        var_value = source_code[assignment_child.start_byte:assignment_child.end_byte]
                
                if var_name and var_value:
                    return f"{var_name}={var_value}"
                elif var_name:
                    return f"{var_name}="
        
        # If we couldn't extract the variable assignment, return an empty string
        # This should not happen in practice
        return ""
    
    def _get_variable_name(self, node: tree_sitter.Node, source_code: str) -> str:
        """Extract variable name from assignment node"""
        for child in node.children:
            if child.type == 'variable_name':
                return source_code[child.start_byte:child.end_byte]
        return ""
    
    def _get_right_value(self, node: tree_sitter.Node, source_code: str) -> str:
        """
        Extract the value being added from the right side of the += operator
        In the tree-sitter-bash AST, the value is the child after the += operator
        """
        # Find the operator position first
        operator_index = -1
        for i, child in enumerate(node.children):
            if child.type == '+=':
                operator_index = i
                break
        
        # If we found the operator, get the next child
        if operator_index >= 0 and operator_index + 1 < len(node.children):
            value_node = node.children[operator_index + 1]
            return source_code[value_node.start_byte:value_node.end_byte]
        return ""
    
    def _is_string_node(self, node: tree_sitter.Node) -> bool:
        """Check if a node is a string literal"""
        return node.type == 'string'
    
    def _get_right_value_node_type(self, node: tree_sitter.Node) -> str:
        """Get the type of node of the right side value"""
        operator_index = -1
        for i, child in enumerate(node.children):
            if child.type == '+=':
                operator_index = i
                break
        
        if operator_index >= 0 and operator_index + 1 < len(node.children):
            return node.children[operator_index + 1].type
        return ""
    
    def _generate_posix_code(self, node: tree_sitter.Node, source_code: str, integer_vars: Set[str]) -> str:
        """Generate POSIX-compliant code for += assignments"""
        var_name = self._get_variable_name(node, source_code)
        right_value = self._get_right_value(node, source_code)
        right_value_type = self._get_right_value_node_type(node)
        
        # Check if this is an integer variable
        if var_name in integer_vars:
            # For integer variables, use arithmetic expansion
            return f"{var_name}=$(({var_name} + {right_value}))"
        else:
            # For string variables, use string concatenation
            # Properly handle quotes based on the type of the right value
            if right_value_type == 'string':
                # For string literals, keep the quotes
                return f"{var_name}=${{{var_name}}}{right_value}"
            elif right_value_type == 'number':
                # For numbers, no quotes needed
                return f"{var_name}=${{{var_name}}}{right_value}"
            else:
                # For other types (variables, expressions, etc.), add quotes to preserve them
                return f"{var_name}=${{{var_name}}}\"{right_value}\""