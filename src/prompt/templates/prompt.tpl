你是一个精通Bash语法和POSIX Shell规范的代码转换器开发者。我需要你根据以下规则，编写一个Python程序，使用`tree-sitter-bash`的API，将Bash代码中的【$feature_name】语法转换为等效的POSIX Shell实现。请严格按照以下结构和要求生成代码：

---

### **任务说明**

1. **目标**：将Bash代码中的 `$feature_name` 语法替换为等效的POSIX Shell实现。
2. **输入**：包含`$feature_name`的Bash代码片段。
3. **输出**：转换后的POSIX Shell代码，保留原有逻辑，但移除对`$feature_name`的依赖。

---

### **语法特性转换规则**

$feature_rules

---

### **输入输出转换示例**

**输入Bash代码**：

```
$bash_example
```

**输出POSIX代码**：

```
$posix_example
```

---

### **代码要求**

- **使用 `tree-sitter-bash`**：通过解析Bash代码的AST（抽象语法树），定位 `$feature_name` 的语法节点。

- **继承基类**：所有转换器必须继承自 `BaseMutator`：

  ```python
  class BaseMutator(ABC):
      #  be overridden by subclasses
      NAME = "base_mutator"  # 转换器名称
      DESCRIPTION = "基础转换器"  # 转换器描述
      TARGET_FEATURES = set()    # 目标Bash特性集合
      
      def __init__(self, parser=None):
          self.parser = parser or initialize_parser()
  
      @abstractmethod
      def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
          """
          Core method: parse AST and replace code
          
          Args:
              source_code: 需要转换的源代码
              context: 可选的上下文信息，包含前序转换器的信息
              
          Returns:
              转换后的代码和更新后的上下文信息
          """
          # patches = []
          # ast = self.parser.parse(bytes(source_code, "utf8"))
          # ...
          # return self.apply_patches(source_code, patches), context
          pass
  
      def apply_patches(self, source_code: str, patches: list) -> str:
          """Apply code replacement patches (shared logic for all mutators)"""
          patches.sort(reverse=True, key=lambda x: x[0])
          for start, end, replacement in patches:
              source_code = source_code[:start] + replacement + source_code[end:]
          return source_code
  ```

- **具体Mutator类实现**：

  ```python
  class {feature}Mutator(BaseMutator):
      # 定义转换器基本信息
      NAME = "{feature}_mutator"  # 转换器名称
      DESCRIPTION = "将Bash {feature} 转换为 POSIX兼容语法"  # 转换器描述
      TARGET_FEATURES = {"{feature}"}  # 目标Bash特性集合
      
      # 定义目标节点类型（如进程替换的node.type为"process_substitution"）
      target_node_types = ["{对应的tree-sitter节点类型}"]
      
      def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
          """
          将Bash {feature} 语法转换为POSIX兼容代码
          
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
  ```

- **临时文件处理**（如需要）: 临时文件变量名用哈希方式命名，调用sh命令生成唯一的临时文件（例如用`mktemp`或`$$`），并确保清理。
- **增强上下文追踪**: 确保所有被识别的变量能被正确地在后续引用中转换

------

### **约束条件**

1. **仅处理目标语法**：不修改其他无关代码。若没有目标代码需要修改，则不做任何处理。
2. **继承BaseMutator**：必须从项目中已定义的`BaseMutator`继承，确保与转换链兼容。
3. **节点类型驱动**：通过`target_node_types`定义需要处理的语法节点类型，而非tree-sitter query。
4. **补丁顺序**：使用`apply_patches`方法处理代码替换，确保偏移量正确。
5. **上下文维护**：通过`context`参数记录已转换特性，方便转换链中后续转换器使用。
6. **临时文件安全**：确保生成的临时文件名唯一，并添加清理逻辑（如`trap 'rm -f tmp_0459c' EXIT`）。
7. **兼容性**：生成的POSIX代码需符合ShellCheck规范，避免扩展语法。
8. **LLM输出**：仅仅输出具体的Mutator类。