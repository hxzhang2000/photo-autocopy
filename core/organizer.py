"""
照片整理核心逻辑模块

提供 PhotoOrganizer 类用于按日期整理照片。
支持干运行模式和操作日志记录。
"""

import os
import shutil
import datetime
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional

from .config import AppConfig
from .exif import is_photo_file, get_photo_date


@dataclass
class OrganizeResult:
    """整理结果统计"""
    
    total_files: int = 0
    photo_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
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


class PhotoOrganizer:
    """
    照片整理器
    
    按拍摄日期将照片整理到 YYYYMMDD 子目录。
    """
    
    def __init__(self, config: AppConfig, callback: Optional[Callable] = None):
        """
        初始化整理器
        
        Args:
            config: 应用配置
            callback: 进度回调函数 callback(current, total, filename)
        """
        self.config = config
        self.callback = callback
        self.result = OrganizeResult()
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """配置日志"""
        self.logger = logging.getLogger('PhotoOrganizer')
        self.logger.setLevel(logging.INFO)
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（如果配置了日志文件）
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
        
        # 收集文件
        self.logger.info(f"正在扫描目录: {self.config.source_path}")
        all_files = list(self._collect_files())
        self.result.total_files = len(all_files)
        self.logger.info(f"共发现 {self.result.total_files} 个文件")
        
        # 处理文件
        for i, file_path in enumerate(all_files):
            self._report_progress(i + 1, self.result.total_files, Path(file_path).name)
            
            if not is_photo_file(file_path):
                continue
            
            self.result.photo_files += 1
            self._process_file(file_path, start_date)
        
        self.result.end_time = datetime.datetime.now()
        self._log_summary()
        
        return self.result
    
    def _collect_files(self):
        """
        收集目录下所有文件（生成器）
        
        Yields:
            文件路径
        """
        source = Path(self.config.source_path)
        if not source.exists():
            return
        
        for item in source.rglob('*'):
            if item.is_file():
                yield str(item)
    
    def _process_file(self, file_path: str, start_date: datetime.datetime) -> None:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            start_date: 开始日期阈值
        """
        # 获取照片日期
        photo_date = get_photo_date(file_path)
        if not photo_date:
            self.result.skipped_files += 1
            return
        
        # 检查日期是否在范围内
        try:
            photo_date_obj = datetime.datetime.strptime(photo_date, '%Y%m%d')
            if photo_date_obj < start_date:
                self.result.skipped_files += 1
                return
        except ValueError:
            self.logger.warning(f"无效的日期格式: {photo_date}")
            self.result.skipped_files += 1
            return
        
        # 计算目标路径
        date_dir = os.path.join(self.config.output_path, photo_date)
        filename = Path(file_path).name
        dest_path = self._get_unique_path(date_dir, filename)
        
        # 执行复制或预览
        if self.config.dry_run:
            self.logger.info(f"[预览] {filename} -> {photo_date}/")
            self.result.processed_files += 1
        else:
            self._copy_file(file_path, dest_path, date_dir)
    
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
        
        如果文件已存在，添加 _1, _2 等后缀。
        
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
        self.logger.info(f"耗时:         {r.elapsed_str}")
        self.logger.info("=" * 40)
