from pathlib import Path
from typing import Dict, Any
from string import Template
from src.utils import initialize_parser

class PromptEngine:
    """Shell转换器的Prompt生成引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化PromptEngine
        Args:
            config: 配置字典，包含模板路径、文档路径等
        """
        self.template_path          = Path(config.get("template_dir")) / "prompt.tpl"
        self.template               = self._load_templates(self.template_path)
        self.refinement_path        = Path(config.get("template_dir")) / "refinement.tpl"
        self.refinement_template    = self._load_templates(self.refinement_path)
        self.docs_dir               = Path(config.get("docs_dir"))
        self.examples_dir           = Path(config.get("examples_dir"))

    def _load_templates(self, template_path:Path) -> Template:
        """加载prompt模板文件"""
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件 {self.template_path} 不存在")
        with open(template_path, "r", encoding="utf-8") as f:
            return Template(f.read())

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

    def _load_ast(self, feature: str) -> str:
        """
        利用tree-sitter API 加载bash对应语法转换示例的AST 
        Args:
            feature: 语法特性名称 (如 'Array', 'ProcessSubstitution'等)
        Returns:
            包含Bash AST的字符串
        """
        bash_code = ""
        example_path = self.examples_dir / f"{feature}_bash.sh"
        if not example_path.exists():
            raise FileNotFoundError(f"示例文件 {example_path} 不存在")
        with open(example_path, "r", encoding="utf-8") as f:
            bash_code = f.read()
        # 使用tree-sitter生成AST
        parser = initialize_parser() 
        tree = parser.parse(bash_code.encode("utf-8"))
        return tree.root_node.sexp()

    def generate_mutator_prompt(self, feature: str) -> str:
        """
        生成用于创建mutator的prompt
        Args:
            feature: 语法特性名称 (如 'Array', 'ProcessSubstitution'等)
        Returns:
            填充后的prompt字符串
        """
        doc_content = self._load_shell_doc(feature)
        examples = self._load_examples(feature)
        prompt = self.template.substitute(
            feature_name=feature,
            feature_rules=doc_content,
            bash_example=examples["bash"],
            posix_example=examples["posix"],
        )
        return prompt
    
    def generate_refinement_prompt(self, feature: str, feedback: str, previous_mutator_code:str) -> str:
        """
        生成用于改进mutator的prompt
        Args:
            feature: 语法特性名称 (如 'Array', 'ProcessSubstitution'等)
            feedback: 上一次生成的mutator的反馈信息
            previous_mutator_code: 上一次生成的mutator代码
        Returns:
            填充后的prompt字符串
        """
        examples = self._load_examples(feature)
        ast = self._load_ast(feature)
        prompt = self.refinement_template.substitute(
            feature_name=feature,
            feedback=feedback,
            previous_code=previous_mutator_code,
            bash_example=examples["bash"],
            bash_ast=ast,
        )
        return prompt 