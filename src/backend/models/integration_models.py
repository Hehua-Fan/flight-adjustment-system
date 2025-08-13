"""
外部系统集成相关的数据模型
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemConnection:
    """系统连接配置"""
    system_name: str
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3 