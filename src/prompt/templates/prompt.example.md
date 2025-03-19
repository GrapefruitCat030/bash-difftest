你是一个精通Bash语法和POSIX Shell规范的代码转换器开发者。我需要你根据以下规则，编写一个Python程序，使用`tree-sitter-bash`的API，将Bash代码中的【ProcessSubstitution】语法转换为等效的POSIX Shell实现。请严格按照以下结构和要求生成代码：

---

### **任务说明**

1. **目标**：将Bash代码中的 `ProcessSubstitution` 语法替换为等效的POSIX Shell实现。
2. **输入**：包含`ProcessSubstitution`的Bash代码片段。
3. **输出**：转换后的POSIX Shell代码，保留原有逻辑，但移除对`ProcessSubstitution`的依赖。

---

### **语法特性转换规则**

| Bash 进程替换语法         | POSIX Shell 实现方法（临时文件）                             |
| :------------------------ | :----------------------------------------------------------- |
| `command <(cmd1)`         | 1. 创建临时文件 2. 运行 `cmd1 > tmpfile` 3. 运行 `command tmpfile` 4. 删除临时文件 |
| `command <(cmd1) <(cmd2)` | 1. 创建两个临时文件 2. 运行 `cmd1 > tmp1` 和 `cmd2 > tmp2` 3. 运行 `command tmp1 tmp2` 4. 删除临时文件 |
| `cmd1 > >(cmd2)`          | 转化为管道，cmd1 \| cmd2 |

---

### **输入输出转换示例**

**输入Bash代码**：

```
arr1=("a" "b" "c") # 无关目标
diff <(ls dir1) <(ls dir2)
arr2=(1 2 3) # 无关目标
cat <(grep "pattern" file1) <(grep "pattern" file2) | sort
cat file | sed 's/foo/bar/g' > >(tee output.txt)
```

**输出POSIX代码**：

```
arr1=("a" "b" "c") # 无关目标

tmp1=$(mktemp)
ls dir1 > "$tmp1"
tmp2=$(mktemp)
ls dir2 > "$tmp2"
diff "$tmp1" "$tmp2"
rm -f "$tmp1" "$tmp2"

arr2=(1 2 3) # 无关目标

tmp3=$(mktemp)
grep "pattern" file1 > "$tmp3"
tmp4=$(mktemp)
grep "pattern" file2 > "$tmp4"
cat "$tmp3" "$tmp4" | sort
rm -f "$tmp3" "$tmp4"

tmp5=$(mktemp)
sed 's/foo/bar/g' file > "$tmp5"
tee output.txt < "$tmp5"
rm -f "$tmp5"
```

---

### **代码要求**

- **使用 `tree-sitter-bash`**：通过解析Bash代码的AST（抽象语法树），定位 `ProcessSubstitution` 的语法节点。

- **继承基类**：所有转换器必须继承自 `BaseMutator`：

  ```python
  import tree_sitter
  from abc import ABC, abstractmethod
  from tree_sitter import Parser
  from typing import Any, Dict, Optional, Tuple
  
  # Initialize tree-sitter parser
  def initialize_parser():
      tree_sitter.Language.build_library(
          'build/my-languages.so',
          ['/user/to/tree-sitter-bash']
      )
      BASH_LANGUAGE = tree_sitter.Language('build/my-languages.so', 'bash')
      parser = tree_sitter.Parser()
      parser.set_language(BASH_LANGUAGE)
      return parser
  
  class BaseMutator(ABC):
      #  be overridden by subclasses
      NAME = "base_transformer"  # 转换器名称
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
  ```

- **临时文件处理**（如需要）：临时文件变量名用哈希方式命名，调用sh命令生成唯一的临时文件（例如用`mktemp`或`$$`），并确保清理。


------

### **约束条件**

1. **仅处理目标语法**：不修改其他无关代码。若没有目标代码需要修改，则不做任何处理。
2. **继承BaseMutator**：必须从项目中已定义的`BaseMutator`继承，确保与转换链兼容。
3. **节点类型驱动**：通过`target_node_types`定义需要处理的语法节点类型，而非tree-sitter query。
4. **补丁顺序**：使用`apply_patches`方法处理代码替换，确保偏移量正确。
5. **上下文维护**：通过`context`参数记录已转换特性，方便转换链中后续转换器使用。
6. **临时文件安全**：确保生成的临时文件名唯一，并添加清理逻辑（如`trap 'rm -f $tmpfile' EXIT`）。
7. **兼容性**：生成的POSIX代码需符合ShellCheck规范，避免扩展语法。