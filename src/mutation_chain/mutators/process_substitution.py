from typing import Any, Dict, Optional, Tuple
from src.mutation_chain import BaseMutator
import tree_sitter

class ProcessSubstitutionMutator(BaseMutator):
    NAME = "process_substitution_mutator"
    DESCRIPTION = "将Bash ProcessSubstitution 转换为 POSIX兼容语法"
    TARGET_FEATURES = {"ProcessSubstitution"}
    
    target_node_types = ["process_substitution"]
    
    def transform(self, source_code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        将Bash ProcessSubstitution 语法转换为POSIX兼容代码
        
        实现两阶段转换：
        1. 首先处理输出进程替换 (>(cmd))，将其转换为管道
        2. 然后处理输入进程替换 (<(cmd))，使用临时文件方法
        """
        context = context or {}
        context['tmp_counter'] = context.get('tmp_counter', 0)
        
        # 第一阶段: 处理输出进程替换 >(cmd)
        output_subst_code, context = self._transform_output_substitutions(source_code, context)
        
        # 第二阶段: 处理输入进程替换 <(cmd)
        final_code, context = self._transform_input_substitutions(output_subst_code, context)
        
        # 更新上下文信息
        transformed_features = context.get('transformed_features', set())
        transformed_features.update(self.TARGET_FEATURES)
        context['transformed_features'] = transformed_features
        
        return final_code, context
    
    def _transform_output_substitutions(self, source_code: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        处理输出进程替换 >(cmd)，将其转换为管道
        """
        patches = []
        
        # 解析AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # 查找所有重定向语句
        redirected_statements = []
        
        def find_redirected_statements(node):
            if node.type == "redirected_statement":
                redirected_statements.append(node)
            for child in node.children:
                find_redirected_statements(child)
        
        find_redirected_statements(root)

        # 处理每个重定向语句，查找包含输出进程替换的情况
        for stmt in redirected_statements:
            # 查找文件重定向
            for child in stmt.children:
                if child.type == "file_redirect":
                    # 检查重定向目标是否是进程替换
                    dest = None
                    for redirect_child in child.children:
                        if redirect_child.type == "process_substitution":
                            dest = redirect_child
                            break
                    
                    if dest and dest.children[0].type == ">(":
                        # 找到输出进程替换
                        # 提取命令部分
                        ps_command = None
                        for ps_child in dest.children:
                            if ps_child.type != ">(" and ps_child.type != ")":
                                ps_command = ps_child.text.decode('utf8')
                                break

                        if ps_command:
                            # 提取左侧命令部分
                            body_node = None
                            for stmt_child in stmt.children:
                                if stmt_child.type == "command":
                                    body_node = stmt_child
                                    break
                            
                            if body_node:
                                body_text = source_code[body_node.start_byte:body_node.end_byte]
                                # 创建管道替换
                                pipeline_text = f"{body_text} | {ps_command}"
                                # 添加补丁，替换整个重定向语句
                                patches.append((stmt.start_byte, stmt.end_byte, pipeline_text))
        
        # 应用补丁
        return self.apply_patches(source_code, patches), context
    
    def _transform_input_substitutions(self, source_code: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        处理输入进程替换 <(cmd)，使用临时文件方法
        """
        patches = []
        
        # 解析AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # 收集所有ProcessSubstitution节点
        process_subst_nodes = []
        
        def _collect_process_subst(node: tree_sitter.Node):
            if node.type in self.target_node_types:
                # 只处理输入进程替换 <(cmd)
                if node.children and node.children[0].type == "<(":
                    process_subst_nodes.append(node)
            for child in node.children:
                _collect_process_subst(child)
        
        if root:
            _collect_process_subst(root)
        
        # 如果没有发现输入进程替换节点，无需转换
        if not process_subst_nodes:
            return source_code, context
        
        # 处理每个进程替换节点
        command_groups = {}
        pipeline_groups = {}  # 跟踪pipeline节点
        
        for ps_node in process_subst_nodes:
            # 查找command和pipeline节点
            command_node = self._find_parent_command(ps_node)
            pipeline_node = self._find_parent_pipeline(ps_node)
            
            if not command_node:
                continue
            
            # 如果该命令属于pipeline，将所有pipeline相关信息存储起来
            if pipeline_node:
                if pipeline_node.id not in pipeline_groups:
                    pipeline_groups[pipeline_node.id] = {
                        'node': pipeline_node,
                        'commands': set(),  # 存储管道中的所有命令节点
                        'process_substs': []
                    }
                pipeline_groups[pipeline_node.id]['commands'].add(command_node.id)
                pipeline_groups[pipeline_node.id]['process_substs'].append(ps_node)
            
            # 同时也存储每个command的信息
            if command_node.id not in command_groups:
                command_groups[command_node.id] = {
                    'node': command_node,
                    'process_substs': [],
                    'tmp_vars': [],
                    'pipeline_id': pipeline_node.id if pipeline_node else None
                }
            command_groups[command_node.id]['process_substs'].append(ps_node)
        
        # 先处理不在pipeline中的普通命令
        for cmd_id, group in command_groups.items():
            # 如果命令属于pipeline，稍后一起处理
            if group['pipeline_id'] is not None:
                continue
                
            cmd_node = group['node']
            process_substs = group['process_substs']
            
            prefix_code = ""
            suffix_code = ""
            
            for ps_node in process_substs:
                # 提取进程替换内的命令内容
                command_content = ""
                for child in ps_node.children:
                    if child.type == "command":
                        command_content = child.text.decode('utf8')
                        break
                
                if not command_content:
                    continue
                
                context['tmp_counter'] += 1
                tmp_var = f"tmp{context['tmp_counter']}"
                group['tmp_vars'].append(tmp_var)
                
                prefix_code += f"{tmp_var}=$(mktemp)\n"
                prefix_code += f"{command_content} > \"${tmp_var}\"\n"
                # 替换进程替换为临时文件
                patches.append((ps_node.start_byte, ps_node.end_byte, f"\"${tmp_var}\""))
                
                # 添加临时文件清理代码
                suffix_code += f"\nrm \"${tmp_var}\"\n"
            
            # 添加前缀和后缀代码
            if prefix_code:
                patches.append((cmd_node.start_byte, cmd_node.start_byte, prefix_code))
            if suffix_code:
                patches.append((cmd_node.end_byte, cmd_node.end_byte, suffix_code))
        
        # 处理pipeline
        for pipe_id, pipe_group in pipeline_groups.items():
            pipeline_node = pipe_group['node']
            pipeline_text = source_code[pipeline_node.start_byte:pipeline_node.end_byte]
            
            # 为pipeline添加前缀代码
            prefix_code = ""
            # 临时文件声明和创建在管道前面
            for ps_node in pipe_group['process_substs']:
                command_content = ""
                for child in ps_node.children:
                    if child.type == "command":
                        command_content = child.text.decode('utf8')
                        break
                
                if not command_content:
                    continue
                
                context['tmp_counter'] += 1
                tmp_var = f"tmp{context['tmp_counter']}"
                
                prefix_code += f"{tmp_var}=$(mktemp)\n"
                prefix_code += f"{command_content} > \"${tmp_var}\"\n"
                # 替换进程替换为临时文件
                patches.append((ps_node.start_byte, ps_node.end_byte, f"\"${tmp_var}\""))
            
            # 临时文件清理放在管道执行后
            suffix_code = "\n"
            for ps_node in pipe_group['process_substs']:
                context['tmp_counter'] += 1
                tmp_var = f"tmp{context['tmp_counter'] - len(pipe_group['process_substs'])}"
                suffix_code += f"rm -f \"${tmp_var}\"\n"
                
            if prefix_code:
                patches.append((pipeline_node.start_byte, pipeline_node.start_byte, prefix_code))
            if suffix_code:
                patches.append((pipeline_node.end_byte, pipeline_node.end_byte, suffix_code))
        
        # 应用补丁并返回结果
        return self.apply_patches(source_code, patches), context
    
    def _find_parent_command(self, node: tree_sitter.Node) -> Optional[tree_sitter.Node]:
        """查找包含进程替换的命令节点"""
        current = node
        while current.parent:
            if current.type == "command":
                return current
            current = current.parent
        return None
    
    def _find_parent_pipeline(self, node: tree_sitter.Node) -> Optional[tree_sitter.Node]:
        """查找包含进程替换的管道节点"""
        current = node
        while current.parent:
            if current.type == "pipeline":
                return current
            current = current.parent
        return None

