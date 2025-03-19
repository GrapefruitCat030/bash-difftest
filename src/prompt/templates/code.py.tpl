class {特性名称}Mutator(BaseMutator):
    # 定义转换器基本信息
    NAME = "{特性名称}_transformer"  # 转换器名称
    DESCRIPTION = "将Bash {特性名称} 转换为 POSIX兼容语法"  # 转换器描述
    TARGET_FEATURES = {"{特性名称}"}  # 目标Bash特性集合
    
    target_node_types = ["{对应的tree-sitter节点类型}"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash {特性名称} 语法转换为POSIX兼容代码
        
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
                # 生成POSIX等效代码，并记录替换位置
                posix_code = self._generate_posix_code(node, source_code)
                patches.append((node.start_byte, node.end_byte, posix_code))
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
        # 这里实现特定语法的转换逻辑