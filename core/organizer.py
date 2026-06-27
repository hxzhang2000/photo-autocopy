"""
照片整理核心逻辑模块

提供 PhotoOrganizer 类用于按日期整理照片。
支持干运行模式、操作日志记录和 RAW+JPEG 配对。
"""

import os
import shutil
import datetime
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional
from collections import defaultdict

from .config import AppConfig
from .exif import (
    is_photo_file, is_raw_file, is_jpeg_file,
    get_photo_date, get_photo_timestamp, get_file_base_name
)


@dataclass
class OrganizeResult:
    """整理结果统计"""
    
    total_files: int = 0
    photo_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    paired_files: int = 0  # RAW+JPEG 配对数量
    stopped: bool = False
    start_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    end_time: Optional[datetime.datetime] = None
    
    @property
    def elapsed_time(self) -> datetime.timedelta:
        """计算耗时"""
        end = self.end_time or datetime.datetime.now()
        return end - self.start_time
    
    @property
    def elapsed_str(self) -> str:
        """格式化耗时字符串"""
        elapsed = self.elapsed_time
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分{seconds}秒"
        else:
            return f"{seconds}秒"


@dataclass
class PhotoFile:
    """照片文件信息"""
    
    path: str
    filename: str
    base_name: str
    is_raw: bool
    is_jpeg: bool
    timestamp: Optional[datetime.datetime] = None
    date: Optional[str] = None
    
    @classmethod
    def from_path(cls, file_path: str) -> 'PhotoFile':
        """从文件路径创建 PhotoFile"""
        filename = Path(file_path).name
        return cls(
            path=file_path,
            filename=filename,
            base_name=get_file_base_name(filename),
            is_raw=is_raw_file(filename),
            is_jpeg=is_jpeg_file(filename),
            timestamp=get_photo_timestamp(file_path),
            date=get_photo_date(file_path)
        )


@dataclass
class PhotoGroup:
    """照片分组（RAW+JPEG 配对）"""
    
    base_name: str
    raw_files: list[PhotoFile] = field(default_factory=list)
    jpeg_files: list[PhotoFile] = field(default_factory=list)
    
    @property
    def is_paired(self) -> bool:
        """是否为 RAW+JPEG 配对"""
        return len(self.raw_files) > 0 and len(self.jpeg_files) > 0
    
    @property
    def primary_file(self) -> PhotoFile:
        """获取主文件（优先 JPEG，用于确定日期）"""
        if self.jpeg_files:
            return self.jpeg_files[0]
        return self.raw_files[0]
    
    @property
    def all_files(self) -> list[PhotoFile]:
        """获取所有文件"""
        return self.jpeg_files + self.raw_files


class PhotoOrganizer:
    """
    照片整理器
    
    按拍摄日期将照片整理到 YYYYMMDD 子目录。
    支持 RAW+JPEG 配对，确保同一拍摄的文件在同一目录。
    """
    
    # 时间戳容差（秒），用于判断是否为同一拍摄
    TIMESTAMP_TOLERANCE_SECONDS = 5
    
    def __init__(
        self,
        config: AppConfig,
        callback: Optional[Callable[[int, int, str], None]] = None,
        stop_callback: Optional[Callable[[], bool]] = None
    ):
        """
        初始化整理器
        
        Args:
            config: 应用配置
            callback: 进度回调函数 callback(current, total, filename)
            stop_callback: 停止检查回调，返回 True 表示应停止
        """
        self.config = config
        self.callback = callback
        self.stop_callback = stop_callback
        self.result = OrganizeResult()
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """配置日志"""
        logger_name = f'PhotoOrganizer_{id(self)}'
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            if self.config.log_file:
                try:
                    file_handler = logging.FileHandler(
                        self.config.log_file,
                        encoding='utf-8'
                    )
                    file_handler.setLevel(logging.DEBUG)
                    file_formatter = logging.Formatter(
                        '%(asctime)s - %(levelname)s - %(message)s'
                    )
                    file_handler.setFormatter(file_formatter)
                    self.logger.addHandler(file_handler)
                except Exception as e:
                    self.logger.warning(f"无法创建日志文件: {e}")
    
    def organize(self) -> OrganizeResult:
        """
        执行照片整理
        
        Returns:
            整理结果统计
        """
        self.result = OrganizeResult()
        self.result.start_time = datetime.datetime.now()
        
        # 验证配置
        errors = self.config.validate()
        if errors:
            for error in errors:
                self.logger.error(f"配置错误: {error}")
            return self.result
        
        # 确保输出目录存在
        if not self.config.dry_run:
            os.makedirs(self.config.output_path, exist_ok=True)
        
        # 解析开始日期
        start_date = self.config.parse_start_date()
        
        # 收集并分组文件
        self.logger.info(f"正在扫描目录: {self.config.source_path}")
        photo_groups = self._collect_and_group_files()
        self.result.total_files = sum(len(g.all_files) for g in photo_groups)
        self.logger.info(f"共发现 {self.result.total_files} 个文件")
        self.logger.info(f"识别为 {len(photo_groups)} 个照片组（含 RAW+JPEG 配对）")
        
        # 处理文件组
        processed_count = 0
        for group in photo_groups:
            # 检查是否需要停止
            if self._should_stop():
                self.result.stopped = True
                self.logger.info("用户已停止处理")
                break
            
            processed_count += 1
            self._report_progress(
                processed_count,
                len(photo_groups),
                group.primary_file.filename
            )
            
            self.result.photo_files += len(group.all_files)
            self._process_group(group, start_date)
        
        self.result.end_time = datetime.datetime.now()
        self._log_summary()
        
        return self.result
    
    def _should_stop(self) -> bool:
        """检查是否应该停止"""
        if self.stop_callback:
            return self.stop_callback()
        return False
    
    def _collect_and_group_files(self) -> list[PhotoGroup]:
        """
        收集文件并按基础名称分组
        
        分组逻辑：
        1. 相同基础名称的文件归为一组（如 IMG_1234.nef 和 IMG_1234.jpg）
        2. 如果基础名称不同，但时间戳在容差范围内，也归为一组
        
        Returns:
            PhotoGroup 列表
        """
        source = Path(self.config.source_path)
        if not source.exists():
            return []
        
        # 收集所有照片文件
        photo_files: list[PhotoFile] = []
        for item in source.rglob('*'):
            if item.is_file() and is_photo_file(item.name):
                photo_files.append(PhotoFile.from_path(str(item)))
        
        # 按基础名称分组
        name_groups: dict[str, list[PhotoFile]] = defaultdict(list)
        for pf in photo_files:
            name_groups[pf.base_name].append(pf)
        
        # 构建 PhotoGroup 列表
        groups: list[PhotoGroup] = []
        used_files: set[str] = set()
        
        # 第一轮：按基础名称精确匹配
        for base_name, files in name_groups.items():
            raw_files = [f for f in files if f.is_raw]
            jpeg_files = [f for f in files if f.is_jpeg]
            
            group = PhotoGroup(
                base_name=base_name,
                raw_files=raw_files,
                jpeg_files=jpeg_files
            )
            groups.append(group)
            
            for f in files:
                used_files.add(f.path)
        
        # 第二轮：尝试按时间戳匹配未配对的 RAW 文件
        unmatched_raw = [
            g.raw_files[0] for g in groups
            if not g.is_paired and g.raw_files
        ]
        unmatched_jpeg = [
            g.jpeg_files[0] for g in groups
            if not g.is_paired and g.jpeg_files
        ]
        
        for raw_file in unmatched_raw:
            if not raw_file.timestamp:
                continue
            
            for jpeg_file in unmatched_jpeg:
                if not jpeg_file.timestamp:
                    continue
                
                # 检查时间戳是否在容差范围内
                time_diff = abs((raw_file.timestamp - jpeg_file.timestamp).total_seconds())
                if time_diff <= self.TIMESTAMP_TOLERANCE_SECONDS:
                    # 找到配对，合并到 JPEG 所在的组
                    for group in groups:
                        if jpeg_file in group.jpeg_files:
                            group.raw_files.append(raw_file)
                            break
                    
                    # 从原组中移除
                    for group in groups:
                        if raw_file in group.raw_files:
                            group.raw_files.remove(raw_file)
                            break
                    
                    self.logger.info(
                        f"时间戳配对: {raw_file.filename} <-> {jpeg_file.filename} "
                        f"(差异 {time_diff:.1f}秒)"
                    )
                    break
        
        # 移除空组
        groups = [g for g in groups if g.all_files]
        
        return groups
    
    def _process_group(self, group: PhotoGroup, start_date: datetime.datetime) -> None:
        """
        处理一个照片组
        
        Args:
            group: 照片组
            start_date: 开始日期阈值
        """
        # 使用主文件的日期
        primary = group.primary_file
        photo_date = primary.date
        
        if not photo_date:
            self.result.skipped_files += len(group.all_files)
            return
        
        # 检查日期是否在范围内
        try:
            photo_date_obj = datetime.datetime.strptime(photo_date, '%Y%m%d')
            if photo_date_obj < start_date:
                self.result.skipped_files += len(group.all_files)
                return
        except ValueError:
            self.logger.warning(f"无效的日期格式: {photo_date}")
            self.result.skipped_files += len(group.all_files)
            return
        
        # 计算目标目录
        date_dir = os.path.join(self.config.output_path, photo_date)
        
        # 处理组内所有文件
        if group.is_paired:
            self.result.paired_files += 1
            if self.config.dry_run:
                self.logger.info(
                    f"[预览] 配对: {', '.join(f.filename for f in group.all_files)} "
                    f"-> {photo_date}/"
                )
        
        for photo_file in group.all_files:
            self._process_file(photo_file, date_dir, photo_date)
    
    def _process_file(
        self,
        photo_file: PhotoFile,
        date_dir: str,
        photo_date: str
    ) -> None:
        """
        处理单个文件
        
        Args:
            photo_file: 照片文件信息
            date_dir: 目标日期目录
            photo_date: 日期字符串
        """
        dest_path = self._get_unique_path(date_dir, photo_file.filename)
        
        if self.config.dry_run:
            if not photo_file.is_raw:  # RAW 文件在配对时已记录
                self.logger.info(f"[预览] {photo_file.filename} -> {photo_date}/")
            self.result.processed_files += 1
        else:
            self._copy_file(photo_file.path, dest_path, date_dir)
    
    def _copy_file(self, src: str, dest: str, date_dir: str) -> None:
        """
        复制文件到目标目录
        
        Args:
            src: 源文件路径
            dest: 目标文件路径
            date_dir: 日期目录路径
        """
        try:
            os.makedirs(date_dir, exist_ok=True)
            shutil.copy2(src, dest)
            self.result.processed_files += 1
        except PermissionError:
            self.logger.error(f"无权限复制文件: {Path(src).name}")
            self.result.failed_files += 1
        except OSError as e:
            self.logger.error(f"复制文件失败 {Path(src).name}: {e}")
            self.result.failed_files += 1
    
    def _get_unique_path(self, directory: str, filename: str) -> str:
        """
        获取唯一文件路径（避免覆盖）
        
        Args:
            directory: 目标目录
            filename: 文件名
            
        Returns:
            唯一文件路径
        """
        base = Path(filename).stem
        ext = Path(filename).suffix
        dest = os.path.join(directory, filename)
        
        if not os.path.exists(dest):
            return dest
        
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            dest = os.path.join(directory, new_name)
            if not os.path.exists(dest):
                return dest
            counter += 1
    
    def _report_progress(self, current: int, total: int, filename: str) -> None:
        """
        报告处理进度
        
        Args:
            current: 当前序号
            total: 总数
            filename: 当前文件名
        """
        if self.callback:
            self.callback(current, total, filename)
    
    def _log_summary(self) -> None:
        """输出处理摘要"""
        r = self.result
        
        self.logger.info("")
        self.logger.info("=" * 40)
        self.logger.info("照片整理完成")
        self.logger.info("-" * 40)
        self.logger.info(f"总文件数:     {r.total_files}")
        self.logger.info(f"照片文件数:   {r.photo_files}")
        self.logger.info(f"成功处理:     {r.processed_files}")
        self.logger.info(f"跳过文件:     {r.skipped_files}")
        self.logger.info(f"失败文件:     {r.failed_files}")
        self.logger.info(f"RAW+JPEG配对: {r.paired_files}")
        if r.stopped:
            self.logger.info("状态:         用户已停止")
        self.logger.info(f"耗时:         {r.elapsed_str}")
        self.logger.info("=" * 40)
