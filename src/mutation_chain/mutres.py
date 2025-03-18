from typing import Dict

class MutateResult:
    """转换结果类，用于传递和合并转换信息"""
    def __init__(self, text: str, transformed: bool = False, metadata: Dict = None):
        self.text = text  # 转换后的文本
        self.transformed = transformed  # 是否已被转换
        self.metadata = metadata or {}  # 附加元数据
    
    def __bool__(self):
        return self.transformed
    
    def merge(self, other: 'MutateResult') -> 'MutateResult':
        """合并两个转换结果"""
        # 如果当前结果未转换，采用其他结果
        if not self.transformed and other.transformed:
            return other
        
        # 如果其他结果未转换，保持当前结果
        if not other.transformed:
            return self
        
        # 如果两者都已转换，需要合并元数据
        merged_metadata = self.metadata.copy()
        for key, value in other.metadata.items():
            if key in merged_metadata and isinstance(value, list) and isinstance(merged_metadata[key], list):
                merged_metadata[key].extend(value)
            else:
                merged_metadata[key] = value
                
        return MutateResult(other.text, True, merged_metadata)
