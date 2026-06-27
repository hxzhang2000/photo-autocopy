"""
photo-autocopy 核心模块

提供照片整理的核心功能：
- config: 配置管理
- exif: EXIF 日期提取
- organizer: 文件整理逻辑
"""

from .config import AppConfig
from .exif import get_photo_date, is_photo_file, PHOTO_EXTENSIONS
from .organizer import PhotoOrganizer, OrganizeResult

__all__ = [
    'AppConfig',
    'get_photo_date',
    'is_photo_file',
    'PHOTO_EXTENSIONS',
    'PhotoOrganizer',
    'OrganizeResult',
]
