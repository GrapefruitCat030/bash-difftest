from typing import Any, Dict, Optional, Tuple, List
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
        1. 首先处理输出进程替换 (>(cmd))，使用临时文件方法
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
        处理输出进程替换 >(cmd)，使用临时文件方法
        
        转换规则：
        command > >(cmd_seq1) > >(cmd_seq2) > >(cmd_seq3)
        转换为：
        1. tmp=$(mktemp)
        2. command > "$tmp"
        3. (cmd_seq1) < "$tmp"; (cmd_seq2) < "$tmp"; (cmd_seq3) < "$tmp"
        4. rm -f "$tmp"
        """
        patches = []
        
        # 解析AST
        ast = self.parser.parse(bytes(source_code, "utf8"))
        root = ast.root_node
        
        # 收集所有输出ProcessSubstitution节点
        output_subst_nodes = []
        
        def _collect_output_subst(node: tree_sitter.Node):
            if node.type in self.target_node_types:
                # 只处理输出进程替换 >(cmd)
                if node.children and node.children[0].type == ">(":
                    output_subst_nodes.append(node)
            for child in node.children:
                _collect_output_subst(child)
        
        if root:
            _collect_output_subst(root)
        
        # 如果没有发现输出进程替换节点，无需转换
        if not output_subst_nodes:
            return source_code, context
        
        # 查找所有重定向语句
        redirected_statements = []
        
        def find_redirected_statements(node):
            if node.type == "redirected_statement":
                # 检查是否包含输出进程替换
                contains_output_subst = False
                for child in node.children:
                    if child.type == "file_redirect":
                        for redirect_child in child.children:
                            if redirect_child.type == "process_substitution" and redirect_child.children[0].type == ">(":
                                contains_output_subst = True
                                break
                
                if contains_output_subst:
                    redirected_statements.append(node)
            
            for child in node.children:
                find_redirected_statements(child)
        
        find_redirected_statements(root)
        
        # 处理每个含有输出进程替换的重定向语句
        for stmt in redirected_statements:
            # 收集命令体和所有输出进程替换
            body_node = None
            output_substitutions = []
            
            for child in stmt.children:
                if child.type == "command" or child.type == "pipeline":
                    body_node = child
                elif child.type == "file_redirect":
                    for redirect_child in child.children:
                        if redirect_child.type == "process_substitution" and redirect_child.children[0].type == ">(":
                            output_substitutions.append(redirect_child)
            
            if body_node and output_substitutions:
                # 获取命令体文本
                body_text = source_code[body_node.start_byte:body_node.end_byte]
                
                # 创建临时文件
                context['tmp_counter'] += 1
                tmp_var = f"tmp{context['tmp_counter']}"
                
                # 构建转换后的代码
                prefix_code = f"{tmp_var}=$(mktemp)\n"
                prefix_code += f"{body_text} > \"${tmp_var}\"\n"
                
                # 构建从临时文件读取的命令序列
                suffix_code = ""
                for ps_node in output_substitutions:
                    # 提取进程替换中的命令序列
                    cmd_start = ps_node.children[0].end_byte  # >( 后面的位置
                    cmd_end = ps_node.children[-1].start_byte  # ) 前面的位置
                    command_content = source_code[cmd_start:cmd_end].strip()
                    
                    if command_content:
                        suffix_code += f"( {command_content}; ) < \"${tmp_var}\"\n"
                
                # 添加临时文件清理代码
                suffix_code += f"rm -f \"${tmp_var}\"\n"
                
                # 检查整个语句是否在pipeline或其他重定向中
                parent_pipeline = self._find_parent_pipeline(stmt)
                parent_redirected = self._find_parent_redirected_statement(stmt)
                has_final_redirect = False
                
                # 检查该重定向语句后是否还有其他重定向
                for child in stmt.children:
                    if child.type == "file_redirect":
                        has_process_subst = False
                        for redirect_child in child.children:
                            if redirect_child.type == "process_substitution":
                                has_process_subst = True
                                break
                        
                        if not has_process_subst:
                            has_final_redirect = True
                            # 保存这个普通重定向用于后续处理
                            final_redirect = source_code[child.start_byte:child.end_byte]
                
                # 生成替换代码
                replacement = prefix_code + suffix_code
                
                # 若在pipeline中，需要保留pipeline结构
                if parent_pipeline:
                    # 在pipeline中，保留管道符号和后续命令
                    pipe_start = None
                    for i, pipe_child in enumerate(parent_pipeline.children):
                        if pipe_child.type == "|" and pipe_child.start_byte > stmt.end_byte:
                            pipe_start = pipe_child.start_byte
                            break
                    
                    if pipe_start:
                        pipe_text = source_code[pipe_start:parent_pipeline.end_byte]
                        replacement += pipe_text
                
                # 添加补丁，替换整个重定向语句
                patches.append((stmt.start_byte, stmt.end_byte, replacement))
            
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
        redirected_statement_groups = {}  # 跟踪重定向语句节点
        
        for ps_node in process_subst_nodes:
            # 查找command、pipeline和redirected_statement节点
            command_node = self._find_parent_command(ps_node)
            pipeline_node = self._find_parent_pipeline(ps_node)
            redirected_statement_node = self._find_parent_redirected_statement(ps_node)

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

            # 如果该命令属于redirected_statement，将所有相关信息存储起来
            if redirected_statement_node:
                if redirected_statement_node.id not in redirected_statement_groups:
                    redirected_statement_groups[redirected_statement_node.id] = {
                        'node': redirected_statement_node,
                        'commands': set(),  # 存储重定向语句中的所有命令节点
                        'process_substs': []
                    }
                redirected_statement_groups[redirected_statement_node.id]['commands'].add(command_node.id)
                redirected_statement_groups[redirected_statement_node.id]['process_substs'].append(ps_node)
            
            # 同时也存储每个command的信息
            if command_node.id not in command_groups:
                command_groups[command_node.id] = {
                    'node': command_node,
                    'process_substs': [],
                    'tmp_vars': [],
                    'pipeline_id': pipeline_node.id if pipeline_node else None,
                    'redirected_statement_id': redirected_statement_node.id if redirected_statement_node else None
                }
            command_groups[command_node.id]['process_substs'].append(ps_node)

        # 处理不在pipeline和重定向语句中的普通命令
        for cmd_id, group in command_groups.items():
            # 如果命令属于pipeline或redirected_statement，稍后一起处理
            if group['pipeline_id'] is not None or group['redirected_statement_id'] is not None:
                continue
                
            cmd_node = group['node']
            process_substs = group['process_substs']
            
            prefix_code = ""
            suffix_code = ""
            
            for ps_node in process_substs:
                # 提取整个进程替换中的命令序列（可能包含多个命令）
                # 定位命令序列的开始和结束位置
                cmd_start = ps_node.children[0].end_byte  # <( 后面的位置
                cmd_end = ps_node.children[-1].start_byte  # ) 前面的位置
                
                # 提取完整命令序列
                command_content = source_code[cmd_start:cmd_end].strip()
                
                if not command_content:
                    continue
                
                context['tmp_counter'] += 1
                tmp_var = f"tmp{context['tmp_counter']}"
                group['tmp_vars'].append(tmp_var)
                
                prefix_code += f"{tmp_var}=$(mktemp)\n"
                # 使用小括号将多个命令组合在一起
                prefix_code += f"{{ {command_content}; }} > \"${tmp_var}\"\n"
                # 替换进程替换为临时文件
                patches.append((ps_node.start_byte, ps_node.end_byte, f"\"${tmp_var}\""))
                
                # 添加临时文件清理代码
                suffix_code += f"rm -f \"${tmp_var}\"\n"
            
            # 添加前缀和后缀代码
            if prefix_code:
                patches.append((cmd_node.start_byte, cmd_node.start_byte, prefix_code))
            if suffix_code:
                patches.append((cmd_node.end_byte, cmd_node.end_byte, "\n" + suffix_code))
        
        # 处理pipeline
        for pipe_id, pipe_group in pipeline_groups.items():
            pipeline_node = pipe_group['node']
            pipeline_text = source_code[pipeline_node.start_byte:pipeline_node.end_byte]
            
            # 为pipeline添加前缀代码
            prefix_code = ""
            # 临时文件声明和创建在管道前面
            for ps_node in pipe_group['process_substs']:
                # 提取整个进程替换中的命令序列（可能包含多个命令）
                cmd_start = ps_node.children[0].end_byte  # <( 后面的位置
                cmd_end = ps_node.children[-1].start_byte  # ) 前面的位置
                
                # 提取完整命令序列
                command_content = source_code[cmd_start:cmd_end].strip()
                
                if not command_content:
                    continue
                
                context['tmp_counter'] += 1
                tmp_var = f"tmp{context['tmp_counter']}"
                
                prefix_code += f"{tmp_var}=$(mktemp)\n"
                prefix_code += f"{{ {command_content}; }} > \"${tmp_var}\"\n"
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
        
        # 处理redirected_statement
        for rs_id, rs_group in redirected_statement_groups.items():
            rs_node = rs_group['node']
            redirected_text = source_code[rs_node.start_byte:rs_node.end_byte]
            
            prefix_code = ""
            # 临时文件声明和创建在重定向语句前面
            for ps_node in rs_group['process_substs']:
                # 提取整个进程替换中的命令序列（可能包含多个命令）
                cmd_start = ps_node.children[0].end_byte  # <( 后面的位置
                cmd_end = ps_node.children[-1].start_byte  # ) 前面的位置
                
                # 提取完整命令序列
                command_content = source_code[cmd_start:cmd_end].strip()
                
                if not command_content:
                    continue
                
                context['tmp_counter'] += 1
                tmp_var = f"tmp{context['tmp_counter']}"
                
                prefix_code += f"{tmp_var}=$(mktemp)\n"
                prefix_code += f"{{ {command_content}; }} > \"${tmp_var}\"\n"
                # 替换进程替换为临时文件
                patches.append((ps_node.start_byte, ps_node.end_byte, f"\"${tmp_var}\""))
                
            # 添加临时文件清理代码
            suffix_code = "\n"
            for ps_node in rs_group['process_substs']:
                context['tmp_counter'] += 1
                tmp_var = f"tmp{context['tmp_counter'] - len(rs_group['process_substs'])}"
                suffix_code += f"rm -f \"${tmp_var}\"\n"
            
            # 添加前缀和后缀代码
            if prefix_code:
                patches.append((rs_node.start_byte, rs_node.start_byte, prefix_code))
            if suffix_code:
                patches.append((rs_node.end_byte, rs_node.end_byte, suffix_code))

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

    def _find_parent_redirected_statement(self, node: tree_sitter.Node) -> Optional[tree_sitter.Node]:
        """查找包含进程替换的重定向命令节点"""
        current = node
        while current.parent:
            if current.type == "redirected_statement":
                return current
            current = current.parent
        return None