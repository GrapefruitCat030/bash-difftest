"""
Mutation Chain module for coordinating the application of multiple mutators
"""

import logging
import inspect
import importlib
import tree_sitter
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import BaseMutator
from .mutres import MutateResult

logger = logging.getLogger(__name__)

# 初始化tree-sitter代码部分保持不变...
def initialize_parser():
    tree_sitter.Language.build_library(
        'build/my-languages.so',
        ['/home/njucs/project/shell-metamorphic-testing/tree-sitter-bash']
    )
    BASH_LANGUAGE = tree_sitter.Language('build/my-languages.so', 'bash')
    parser = tree_sitter.Parser()
    parser.set_language(BASH_LANGUAGE)
    return parser

class MutatorRegistry:
    def __init__(self, mutators_path):
        self.mutators_dir = mutators_path
        self.mutators: List[BaseMutator] = []

    def register(self, mutator: BaseMutator):
        self.mutators.append(mutator)
        self.mutators.sort(key=lambda t: t.priority) # 按优先级排序

class MutationChain:
    def __init__(self, config):
        self.parser = initialize_parser()
        self.registry = MutatorRegistry(config["results"]["mutators"])
        self._register_mutators()
        self.debug = False
    
    def _register_mutators(self):
        # 获取mutators目录路径
        mutators_dir = Path(self.registry.mutators_dir)
        
        # 检查目录是否存在
        if not mutators_dir.exists() or not mutators_dir.is_dir():
            logger.warning(f"Mutators目录不存在: {mutators_dir}")
            return
        
        # 扫描所有Python文件
        for py_file in mutators_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # 构建模块名
            module_name = f".mutators.{py_file.stem}"
            
            try:
                # 使用相对导入方式导入模块
                module = importlib.import_module(module_name, package="src.mutation_chain")
                
                # 查找所有BaseMutator的子类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseMutator) and 
                        obj != BaseMutator):
                        
                        # 实例化并注册mutator
                        mutator_instance = obj()
                        self.registry.register(mutator_instance)
                        logger.info(f"已注册变异器: {name}")
                            
            except Exception as e:
                logger.error(f"加载模块 {py_file.name} 时出错: {e}")
    
    def convert(self, seed_file: Path) -> str:
        bash_code = seed_file.read_text(encoding="utf-8")
        source_bytes = bytes(bash_code, 'utf8')
        tree = self.parser.parse(source_bytes)
        
        if self.debug:
            self._print_tree(tree.root_node, source_bytes)
        
        # 全局上下文，用于存储转换过程中的信息
        context = {"arrays": {}, "temp_files": []}
        
        # 执行DFS后序遍历转换
        result = self._transform_node(tree.root_node, source_bytes, context)
        
        # 添加清理临时文件的命令
        if context.get("temp_files"):
            result_text = result.text
            result_text += "\n\n# 清理临时文件\ntrap 'rm -f"
            for temp_file in context["temp_files"]:
                result_text += f" ${{{temp_file}}}"
            result_text += "' EXIT"
            return result_text

        return result.text
    
    def _transform_node(self, node: tree_sitter.Node, source_bytes: bytes, context: Dict) -> MutateResult:
        """使用DFS后序遍历转换节点"""
        # 首先递归处理所有子节点
        children_results = {}
        
        if len(node.children) > 0:
            for i, child in enumerate(node.children):
                child_result = self._transform_node(child, source_bytes, context)
                if child_result.transformed:
                    children_results[i] = child_result
                    
                    # 更新上下文
                    if "arrays" in child_result.metadata:
                        context.setdefault("arrays", {}).update(child_result.metadata["arrays"])
                    if "temp_files" in child_result.metadata:
                        context.setdefault("temp_files", []).extend(child_result.metadata["temp_files"])
        
        # 然后尝试转换当前节点
        for transformer in self.registry.mutators:
            if transformer.can_transform(node, source_bytes, context):
                transformer_result = transformer.transform(node, source_bytes, context, children_results)
                if transformer_result.transformed:
                    if self.debug:
                        print(f"Node {node.type} transformed by {transformer.get_name()}")
                    return transformer_result
        
        # 如果当前节点不需要转换，但有子节点被转换，需要重建节点文本
        if children_results:
            return self._rebuild_node_text(node, source_bytes, children_results)
        
        # 如果没有任何转换发生，返回原始文本
        original_text = source_bytes[node.start_byte:node.end_byte].decode('utf8')
        return MutateResult(original_text, False)
    
    def _rebuild_node_text(self, node: tree_sitter.Node, source_bytes: bytes, 
                          children_results: Dict[int, MutateResult]) -> MutateResult:
        """重建具有已转换子节点的节点文本"""
        result = ""
        cursor = node.start_byte
        
        # 合并元数据
        merged_metadata = {}
        
        for i, child in enumerate(node.children):
            # 添加子节点之前的文本
            if child.start_byte > cursor:
                result += source_bytes[cursor:child.start_byte].decode('utf8')
            
            # 添加子节点文本（原始或已转换）
            if i in children_results:
                child_result = children_results[i]
                result += child_result.text
                
                # 合并子节点的元数据
                for key, value in child_result.metadata.items():
                    if key in merged_metadata and isinstance(merged_metadata[key], list) and isinstance(value, list):
                        merged_metadata[key].extend(value)
                    else:
                        merged_metadata[key] = value
            else:
                result += source_bytes[child.start_byte:child.end_byte].decode('utf8')
            
            cursor = child.end_byte
        
        # 添加最后一个子节点后的原始文本
        if cursor < node.end_byte:
            result += source_bytes[cursor:node.end_byte].decode('utf8')
        
        return MutateResult(result, True, merged_metadata)
    
    def _print_tree(self, node, indent=0, source_bytes=None):
        """调试辅助函数：打印AST结构"""
        node_text = ""
        if source_bytes and node.end_byte <= len(source_bytes):
            node_text = source_bytes[node.start_byte:node.end_byte].decode('utf8')
            if len(node_text) > 30:
                node_text = node_text[:30] + "..."
            node_text = node_text.replace('\n', '\\n')
        
        print('  ' * indent + f"{node.type} - {node_text}")
        for child in node.children:
            self._print_tree(child, indent + 1, source_bytes)