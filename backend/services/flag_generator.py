"""
动态Flag生成服务 - 移植自GZCTF
支持：[GUID]、[TEAM_HASH]、[LEET]、[CLEET] 等占位符
"""

import uuid
import hashlib
import random
from enum import Enum
from typing import Optional, Callable, List, Tuple, Dict
from dataclasses import dataclass


class LeetMode(Enum):
    """Leet转换模式"""
    NONE = 0           # 不转换
    DEFAULT = 1        # 默认转换（无显式标记，无GUID/TEAM_HASH）
    LEET = 2          # [LEET] 标记 - 基础Leet转换
    CLEET = 3         # [CLEET] 标记 - Leet转换+特殊字符


class FlagSegmentType(Enum):
    """Flag段类型"""
    PLAIN_TEXT = 0    # 纯文本（不转换）
    LEET_TEXT = 1     # 需要Leet转换的文本
    TEAM_HASH = 2     # [TEAM_HASH] 占位符
    GUID = 3          # [GUID] 占位符


@dataclass
class FlagSegment:
    """Flag段结构"""
    type: FlagSegmentType
    content: Optional[str] = None  # 用于PlainText/LeetText
    # 对于占位符，content为None


@dataclass
class FlagTemplate:
    """解析后的Flag模板"""
    template: str
    leet_mode: LeetMode
    segments: List[FlagSegment]
    has_sufficient_randomness: bool  # 是否包含GUID或TEAM_HASH


class DynamicFlagGenerator:
    """
    动态Flag生成器
    
    支持的占位符：
    - [GUID]: 生成唯一的GUID（36字符）
    - [TEAM_HASH]: 用提供的team hash替换（12字符）
    - [LEET]: 对花括号内容进行Leet转换
    - [CLEET]: 对花括号内容进行高级Leet转换（含特殊字符）
    
    示例：
    - "flag{[GUID]}" -> "flag{550e8400-e29b-41d4-a716-446655440000}"
    - "flag{hello_[TEAM_HASH]}" -> "flag{hello_abc123def456}"
    - "[LEET]flag{hello}" -> "flag{h3ll0}"
    """
    
    # 基础Leet转换表
    CHAR_MAP = {
        'A': "Aa4", 'B': "Bb68", 'C': "Cc", 'D': "Dd",
        'E': "Ee3", 'F': "Ff1", 'G': "Gg69", 'H': "Hh",
        'I': "Ii1l", 'J': "Jj", 'K': "Kk", 'L': "Ll1I",
        'M': "Mm", 'N': "Nn", 'O': "Oo0", 'P': "Pp",
        'Q': "Qq9", 'R': "Rr", 'S': "Ss5", 'T': "Tt7",
        'U': "Uu", 'V': "Vv", 'W': "Ww", 'X': "Xx",
        'Y': "Yy", 'Z': "Zz2",
        '0': "0oO", '1': "1lI", '2': "2zZ", '3': "3eE",
        '4': "4aA", '5': "5Ss", '6': "6Gb", '7': "7T",
        '8': "8bB", '9': "9g"
    }
    
    # 高级Leet转换表（含特殊字符）
    COMPLEX_CHAR_MAP = {
        'A': "Aa4@", 'B': "Bb6&", 'C': "Cc(", 'D': "Dd",
        'E': "Ee3", 'F': "Ff1", 'G': "Gg69", 'H': "Hh",
        'I': "Ii1l!", 'J': "Jj", 'K': "Kk", 'L': "Ll1I!",
        'M': "Mm", 'N': "Nn", 'O': "Oo0#", 'P': "Pp",
        'Q': "Qq9", 'R': "Rr", 'S': "Ss5$", 'T': "Tt7",
        'U': "Uu", 'V': "Vv", 'W': "Ww", 'X': "Xx",
        'Y': "Yy", 'Z': "Zz2?",
        '0': "0oO#", '1': "1lI|", '2': "2zZ?", '3': "3eE",
        '4': "4aA", '5': "5Ss", '6': "6Gb", '7': "7T",
        '8': "8B&", '9': "9g"
    }
    
    # 模板缓存
    _cache: Dict[str, FlagTemplate] = {}
    
    def __init__(self, template: Optional[str]):
        """初始化生成器"""
        self.raw_template = template
        self.template_obj = self._parse_template(template)
    
    @classmethod
    def _parse_template(cls, template: Optional[str]) -> FlagTemplate:
        """解析模板字符串为结构化对象"""
        if not template:
            return FlagTemplate(
                template="",
                leet_mode=LeetMode.NONE,
                segments=[],
                has_sufficient_randomness=False
            )
        
        # 检查缓存
        if template in cls._cache:
            return cls._cache[template]
        
        # 检测Leet标记
        leet_mode = LeetMode.DEFAULT
        processed_template = template
        
        if template.startswith("[LEET]"):
            leet_mode = LeetMode.LEET
            processed_template = template[6:]
        elif template.startswith("[CLEET]"):
            leet_mode = LeetMode.CLEET
            processed_template = template[7:]
        
        # 解析段
        segments = []
        has_guid_or_hash = False
        brace_depth = 0
        i = 0
        current_segment_start = 0
        
        while i < len(processed_template):
            # 检查占位符
            remaining = processed_template[i:]
            
            if remaining.startswith("[GUID]"):
                # 刷新之前的文本
                if i > current_segment_start:
                    content = processed_template[current_segment_start:i]
                    seg_type = FlagSegmentType.LEET_TEXT if brace_depth > 0 else FlagSegmentType.PLAIN_TEXT
                    segments.append(FlagSegment(type=seg_type, content=content))
                
                # 添加GUID占位符
                segments.append(FlagSegment(type=FlagSegmentType.GUID))
                has_guid_or_hash = True
                i += 6
                current_segment_start = i
                continue
            
            if remaining.startswith("[TEAM_HASH]"):
                # 刷新之前的文本
                if i > current_segment_start:
                    content = processed_template[current_segment_start:i]
                    seg_type = FlagSegmentType.LEET_TEXT if brace_depth > 0 else FlagSegmentType.PLAIN_TEXT
                    segments.append(FlagSegment(type=seg_type, content=content))
                
                # 添加TEAM_HASH占位符
                segments.append(FlagSegment(type=FlagSegmentType.TEAM_HASH))
                has_guid_or_hash = True
                i += 11
                current_segment_start = i
                continue
            
            # 跟踪花括号深度
            if processed_template[i] == '{':
                if brace_depth == 0:
                    # 刷新纯文本段（含'{'）
                    if i >= current_segment_start:
                        content = processed_template[current_segment_start:i+1]
                        segments.append(FlagSegment(type=FlagSegmentType.PLAIN_TEXT, content=content))
                    current_segment_start = i + 1
                brace_depth += 1
            elif processed_template[i] == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    # 刷新Leet文本段（含'}'）
                    if i >= current_segment_start:
                        content = processed_template[current_segment_start:i+1]
                        segments.append(FlagSegment(type=FlagSegmentType.LEET_TEXT, content=content))
                    current_segment_start = i + 1
            
            i += 1
        
        # 刷新剩余文本
        if current_segment_start < len(processed_template):
            content = processed_template[current_segment_start:]
            seg_type = FlagSegmentType.LEET_TEXT if brace_depth > 0 else FlagSegmentType.PLAIN_TEXT
            segments.append(FlagSegment(type=seg_type, content=content))
        
        # 如果有GUID/TEAM_HASH，则不需要Leet提供随机性
        if has_guid_or_hash and leet_mode == LeetMode.DEFAULT:
            leet_mode = LeetMode.NONE
        
        result = FlagTemplate(
            template=processed_template,
            leet_mode=leet_mode,
            segments=segments,
            has_sufficient_randomness=has_guid_or_hash
        )
        
        # 缓存结果
        cls._cache[template] = result
        return result
    
    def generate_with_team_hash(self, team_hash_provider: Callable[[], str]) -> str:
        """
        使用team hash生成flag
        
        Args:
            team_hash_provider: 返回team hash的可调用对象
        """
        if not self.raw_template:
            return f"flag{{{uuid.uuid4()}}}"
        
        cached_hash = [None]  # 用列表来缓存hash值
        
        def resolver():
            if cached_hash[0] is None:
                cached_hash[0] = team_hash_provider()
            return cached_hash[0]
        
        return self._generate_flag(resolver)
    
    def generate_test_flag(self) -> str:
        """为测试生成flag"""
        if not self.raw_template:
            return "flag{GZCTF_dynamic_flag_test}"
        
        return self._generate_flag(lambda: "TestTeamHash")
    
    def generate_random_flag(self) -> str:
        """生成包含随机性的flag"""
        if not self.raw_template:
            return f"flag{{{uuid.uuid4()}}}"
        
        return self._generate_flag(lambda: "TestTeamHash")
    
    def _generate_flag(self, team_hash_resolver: Callable[[], str]) -> str:
        """
        核心flag生成逻辑
        
        Args:
            team_hash_resolver: 返回team hash的可调用对象
        """
        result = []
        apply_leet = self.template_obj.leet_mode != LeetMode.NONE
        char_map = self.COMPLEX_CHAR_MAP if self.template_obj.leet_mode == LeetMode.CLEET else self.CHAR_MAP
        
        for segment in self.template_obj.segments:
            if segment.type == FlagSegmentType.PLAIN_TEXT:
                result.append(segment.content)
            elif segment.type == FlagSegmentType.LEET_TEXT:
                if apply_leet and segment.content:
                    result.append(self._leet_convert(segment.content, char_map))
                else:
                    result.append(segment.content)
            elif segment.type == FlagSegmentType.TEAM_HASH:
                result.append(team_hash_resolver())
            elif segment.type == FlagSegmentType.GUID:
                result.append(str(uuid.uuid4()))
        
        return "".join(result)
    
    @staticmethod
    def _leet_convert(text: str, char_map: Dict[str, str]) -> str:
        """
        Leet转换
        
        Args:
            text: 需要转换的文本
            char_map: 字符映射表
        """
        result = []
        for char in text:
            upper_char = char.upper()
            if upper_char in char_map:
                options = char_map[upper_char]
                result.append(random.choice(options))
            elif char == ' ':
                result.append('_')
            else:
                result.append(char)
        
        return "".join(result)


class ContainerFlagService:
    """容器动态Flag服务"""
    
    @staticmethod
    def generate_dynamic_flag(
        flag_template: Optional[str],
        challenge_id: int,
        user_id: int,
        game_id: int,
        team_id: Optional[int] = None,
        team_hash_salt: Optional[str] = None
    ) -> str:
        """
        为容器生成动态flag
        
        Args:
            flag_template: Flag模板
            challenge_id: 题目ID
            user_id: 用户ID
            game_id: 比赛ID
            team_id: 团队ID（可选）
            team_hash_salt: 团队hash盐值
        
        Returns:
            生成的flag字符串
        """
        generator = DynamicFlagGenerator(flag_template)
        
        # 如果模板为空，使用默认格式
        if not flag_template:
            return f"flag{{{uuid.uuid4()}}}"
        
        # 生成team hash
        def get_team_hash():
            # GZCTF的算法：hash(salt::challenge_id::user_id)
            if team_hash_salt:
                salt_str = f"{team_hash_salt}::{challenge_id}"
            else:
                salt_str = f"game_{game_id}_challenge_{challenge_id}"
            
            user_str = f"{salt_str}::{user_id}"
            hash_obj = hashlib.sha256(user_str.encode())
            return hash_obj.hexdigest()[12:24]  # 取12-24位（12字符）
        
        return generator.generate_with_team_hash(get_team_hash)
    
    @staticmethod
    def generate_test_flag(flag_template: Optional[str]) -> str:
        """为测试生成flag"""
        generator = DynamicFlagGenerator(flag_template)
        return generator.generate_test_flag()
