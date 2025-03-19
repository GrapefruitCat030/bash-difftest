from pathlib import Path
from typing import List, Dict, Optional

class PromptEngine:
    """Shell转换器的Prompt生成引擎"""
    
    def __init__(self, config: Dict):
        """
        初始化PromptEngine
        Args:
            config: 配置字典，包含模板路径、文档路径等
        """
        self.template_path = Path(config["prompt_engine"]["template_dir"]) / "prompt.tpl"
        self.docs_dir = Path(config["prompt_engine"]["docs_dir"])
        self.examples_dir = Path(config["prompt_engine"]["examples_dir"])
        self.template = self._load_templates()

    def _load_templates(self) -> str:
        """加载prompt模板文件"""
        if not self.template_path.exists():
            raise FileNotFoundError(f"模板文件 {self.template_path} 不存在")
        with open(self.template_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_shell_doc(self, feature: str) -> str:
        """
        加载bash和posix两种shell语法转换规则文档
        Args:
            feature: 语法特性名称 (如 'Array', 'ProcessSubstitution'等)
        Returns:
            文档内容字符串
        """
        doc_path = self.docs_dir / f"{feature}.md"
        if not doc_path.exists():
            raise FileNotFoundError(f"文档文件 {doc_path} 不存在")
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_examples(self, feature: str) -> Dict[str, str]:
        """
        加载bash和posix两种shell对应语法转换示例
        Args:
            feature: 语法特性名称 (如 'Array', 'ProcessSubstitution'等)
        Returns:
            包含Bash和POSIX示例代码的字典
        """
        examples = {}
        for shell_type in ["bash", "posix"]:
            example_path = self.examples_dir / f"{feature}_{shell_type}.sh"
            if not example_path.exists():
                raise FileNotFoundError(f"示例文件 {example_path} 不存在")
            with open(example_path, "r", encoding="utf-8") as f:
                examples[shell_type] = f.read()
        return examples

    def generate_mutator_prompt(self, feature: str) -> str:
        """
        生成用于创建mutator的prompt
        Args:
            feature: 语法特性名称 (如 'Array', 'ProcessSubstitution'等)
        Returns:
            填充后的prompt字符串
        """
        # 加载文档和示例
        doc_content = self._load_shell_doc(feature)
        examples = self._load_examples(feature)
        
        # 填充模板
        prompt = self.template.format(
            语法特性名称=feature,
            语法特性对比描述=doc_content,
            示例Bash代码段=examples["bash"],
            对应的POSIX转换结果=examples["posix"]
        )
        return prompt