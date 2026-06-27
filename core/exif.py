"""
EXIF 日期提取模块

提供照片日期提取功能，支持多种格式包括 HEIC/HEIF。
使用 details=False 优化读取性能。
"""

import os
import datetime
from pathlib import Path
from typing import Optional

import exifread


# 支持的照片格式
PHOTO_EXTENSIONS = {
    # 常见格式
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    # RAW 格式
    '.raw', '.nef', '.arw', '.cr2', '.cr3', '.dng',
    # Apple HEIC/HEIF
    '.heic', '.heif',
}

# RAW 格式集合
RAW_EXTENSIONS = {'.raw', '.nef', '.arw', '.cr2', '.cr3', '.dng'}

# JPEG 格式集合
JPEG_EXTENSIONS = {'.jpg', '.jpeg'}

# EXIF 日期标签（按优先级排序）
DATE_TAGS = [
    'EXIF DateTimeOriginal',
    'EXIF DateTimeDigitized',
    'Image DateTime',
]


def is_photo_file(filename: str) -> bool:
    """
    判断文件是否为支持的照片格式
    
    Args:
        filename: 文件名
        
    Returns:
        是否为支持的照片格式
    """
    ext = Path(filename).suffix.lower()
    return ext in PHOTO_EXTENSIONS


def is_raw_file(filename: str) -> bool:
    """
    判断文件是否为 RAW 格式
    
    Args:
        filename: 文件名
        
    Returns:
        是否为 RAW 格式
    """
    ext = Path(filename).suffix.lower()
    return ext in RAW_EXTENSIONS


def is_jpeg_file(filename: str) -> bool:
    """
    判断文件是否为 JPEG 格式
    
    Args:
        filename: 文件名
        
    Returns:
        是否为 JPEG 格式
    """
    ext = Path(filename).suffix.lower()
    return ext in JPEG_EXTENSIONS


def get_photo_date(file_path: str) -> Optional[str]:
    """
    从照片文件中提取拍摄日期
    
    优先从 EXIF 读取，降级使用文件修改时间。
    
    Args:
        file_path: 照片文件路径
        
    Returns:
        日期字符串（YYYYMMDD 格式），失败返回 None
    """
    try:
        # 尝试从 EXIF 读取日期
        exif_date = _read_exif_date(file_path)
        if exif_date:
            return exif_date
        
        # 降级使用文件修改时间
        return _get_mtime_date(file_path)
        
    except Exception as e:
        print(f"无法提取文件日期 {Path(file_path).name}: {e}")
        return None


def get_photo_timestamp(file_path: str) -> Optional[datetime.datetime]:
    """
    从照片文件中提取精确拍摄时间戳
    
    用于 RAW+JPEG 配对，需要精确到秒级。
    优先从 EXIF 读取，降级使用文件修改时间。
    
    Args:
        file_path: 照片文件路径
        
    Returns:
        datetime 对象，失败返回 None
    """
    try:
        # 尝试从 EXIF 读取时间戳
        timestamp = _read_exif_timestamp(file_path)
        if timestamp:
            return timestamp
        
        # 降级使用文件修改时间
        mtime = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(mtime)
        
    except Exception:
        return None


def _read_exif_timestamp(file_path: str) -> Optional[datetime.datetime]:
    """
    从 EXIF 读取精确时间戳
    
    Args:
        file_path: 照片文件路径
        
    Returns:
        datetime 对象，失败返回 None
    """
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        
        # 按优先级尝试获取时间戳
        for tag_name in DATE_TAGS:
            if tag_name in tags:
                date_str = str(tags[tag_name])
                return _parse_exif_timestamp(date_str)
        
        return None
        
    except Exception:
        return None


def _parse_exif_timestamp(date_str: str) -> Optional[datetime.datetime]:
    """
    解析 EXIF 时间戳格式
    
    EXIF 日期格式：YYYY:MM:DD HH:MM:SS
    
    Args:
        date_str: EXIF 日期字符串
        
    Returns:
        datetime 对象，解析失败返回 None
    """
    try:
        # 格式：YYYY:MM:DD HH:MM:SS
        return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except ValueError:
        return None


def _read_exif_date(file_path: str) -> Optional[str]:
    """
    从 EXIF 读取日期
    
    Args:
        file_path: 照片文件路径
        
    Returns:
        日期字符串（YYYYMMDD 格式），失败返回 None
    """
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        
        # 按优先级尝试获取日期
        for tag_name in DATE_TAGS:
            if tag_name in tags:
                date_str = str(tags[tag_name])
                return _parse_exif_date(date_str)
        
        return None
        
    except Exception:
        return None


def _parse_exif_date(date_str: str) -> Optional[str]:
    """
    解析 EXIF 日期格式
    
    EXIF 日期格式：YYYY:MM:DD HH:MM:SS
    转换为：YYYYMMDD
    
    Args:
        date_str: EXIF 日期字符串
        
    Returns:
        YYYYMMDD 格式日期，解析失败返回 None
    """
    try:
        # 分割日期和时间部分
        date_part = date_str.split(' ')[0]
        
        # 验证格式
        if len(date_part) != 10 or date_part.count(':') != 2:
            return None
        
        # 转换 YYYY:MM:DD -> YYYYMMDD
        result = date_part.replace(':', '')
        
        # 验证结果是有效日期
        datetime.datetime.strptime(result, '%Y%m%d')
        
        return result
        
    except (ValueError, IndexError):
        return None


def _get_mtime_date(file_path: str) -> Optional[str]:
    """
    获取文件修改日期
    
    Args:
        file_path: 文件路径
        
    Returns:
        YYYYMMDD 格式日期
    """
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(mtime).strftime('%Y%m%d')
    except Exception:
        return None


def get_file_base_name(filename: str) -> str:
    """
    获取文件的基础名称（不含扩展名）
    
    用于 RAW+JPEG 配对时匹配文件名。
    
    Args:
        filename: 文件名
        
    Returns:
        基础名称（小写）
    """
    return Path(filename).stem.lower()


def get_supported_extensions() -> list[str]:
    """
    获取支持的文件扩展名列表
    
    Returns:
        扩展名列表（带点号，小写）
    """
    return sorted(PHOTO_EXTENSIONS)
