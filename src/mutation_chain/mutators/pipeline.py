from typing import Any, Dict, Optional, Tuple, List
import tree_sitter
from src.mutation_chain import BaseMutator

class PipelineMutator(BaseMutator):
    # Define basic information for the mutator
    NAME = "pipeline_mutator"
    DESCRIPTION = "将Bash Pipeline语法 |& 转换为 POSIX兼容的 2>&1 | 语法"
    TARGET_FEATURES = {"pipeline"}
    
    # The pipeline node itself is what we need to target
    target_node_types = ["pipeline"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash Pipeline语法转换为POSIX兼容代码
        
        Args:
            source_code: 需要转换的源代码
            context: 可选的上下文信息，包含前序转换器的信息
            
        Returns:
            转换后的代码和更新后的上下文信息
        """
        # Initialize context if not provided
        context = context or {}
        patches = []
        
        # Parse AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # Traverse AST to find all pipeline nodes
        def _traverse(node: tree_sitter.Node):
            if node.type in self.target_node_types:
                self._process_pipeline(node, source_code, patches)
            
            # Continue traversal for non-pipeline nodes
            # For pipelines, we handle children internally in _process_pipeline
            if node.type not in self.target_node_types:
                for child in node.children:
                    _traverse(child)
        
        # Execute traversal
        if root:
            _traverse(root)
        
        # Update context information
        transformed_features = context.get('transformed_features', set())
        if patches:
            transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        # Apply patches and return results
        return self.apply_patches(source_code, patches), context
    
    def _process_pipeline(self, pipeline_node: tree_sitter.Node, source_code: str, patches: list):
        """
        处理pipeline节点，找出所有 |& 操作符并替换为 2>&1 |
        
        Args:
            pipeline_node: pipeline节点
            source_code: 原始代码
            patches: 用于存储替换补丁的列表
        """
        # We need to find all |& nodes directly within the pipeline
        pipe_and_err_nodes = []
        
        for i, child in enumerate(pipeline_node.children):
            # Check if this child is a |& node
            if child.type == '|&':
                # Create a patch to replace |& with 2>&1 |
                patches.append((child.start_byte, child.end_byte, "2>&1 |"))
