"""
配置管理模块

提供 AppConfig 类用于管理应用程序配置。
支持从 INI 文件加载和保存配置。
"""

import os
import configparser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# 默认配置值
DEFAULT_SOURCE_PATH = r"D:\照片\原始目录"
DEFAULT_OUTPUT_PATH = r"D:\照片\整理后"
DEFAULT_START_DATE = "20250101"


@dataclass
class AppConfig:
    """应用程序配置"""
    
    source_path: str = DEFAULT_SOURCE_PATH
    output_path: str = DEFAULT_OUTPUT_PATH
    start_date: str = DEFAULT_START_DATE
    dry_run: bool = False
    log_file: Optional[str] = None
    
    @classmethod
    def from_ini(cls, config_file: str = 'config.ini') -> 'AppConfig':
        """
        从 INI 文件加载配置
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            AppConfig 实例
        """
        config = configparser.ConfigParser()
        app_config = cls()
        
        if not os.path.exists(config_file):
            return app_config
        
        try:
            config.read(config_file, encoding='utf-8')
            
            # 加载路径配置
            if 'Paths' in config:
                app_config.source_path = config['Paths'].get('source_path', DEFAULT_SOURCE_PATH)
                app_config.output_path = config['Paths'].get('output_path', DEFAULT_OUTPUT_PATH)
            
            # 加载设置配置
            if 'Settings' in config:
                app_config.start_date = config['Settings'].get('start_date', DEFAULT_START_DATE)
                
        except Exception as e:
            print(f"警告: 读取配置文件失败: {e}")
        
        return app_config
    
    def save_ini(self, config_file: str = 'config.ini') -> None:
        """
        保存配置到 INI 文件
        
        Args:
            config_file: 配置文件路径
        """
        config = configparser.ConfigParser()
        
        config['Paths'] = {
            'source_path': self.source_path,
            'output_path': self.output_path,
        }
        
        config['Settings'] = {
            'start_date': self.start_date,
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
        except Exception as e:
            print(f"错误: 保存配置文件失败: {e}")
    
    def validate(self) -> list[str]:
        """
        验证配置有效性
        
        Returns:
            错误消息列表，空列表表示配置有效
        """
        errors = []
        
        # 验证源路径
        if not self.source_path:
            errors.append("源路径未设置")
        elif not os.path.exists(self.source_path):
            errors.append(f"源路径不存在: {self.source_path}")
        
        # 验证输出路径
        if not self.output_path:
            errors.append("输出路径未设置")
        
        # 验证日期格式
        try:
            self.parse_start_date()
        except ValueError as e:
            errors.append(f"日期格式错误: {e}")
        
        return errors
    
    def parse_start_date(self) -> 'datetime.datetime':
        """
        解析开始日期
        
        Returns:
            datetime 对象
            
        Raises:
            ValueError: 日期格式无效
        """
        import datetime
        
        # 尝试 YYYYMMDD 格式
        try:
            return datetime.datetime.strptime(self.start_date, '%Y%m%d')
        except ValueError:
            pass
        
        # 尝试 YYYY-MM-DD 格式
        try:
            return datetime.datetime.strptime(self.start_date, '%Y-%m-%d')
        except ValueError:
            pass
        
        raise ValueError(f"无效的日期格式: {self.start_date}，请使用 YYYYMMDD 或 YYYY-MM-DD")
    
    def get_app_directory(self) -> str:
        """
        获取程序所在目录（支持 PyInstaller 打包）
        
        Returns:
            程序所在目录路径
        """
        import sys
        
        try:
            if hasattr(sys, '_MEIPASS') or getattr(sys, 'frozen', False):
                # PyInstaller 打包后
                exe_path = os.path.realpath(sys.executable)
                app_dir = os.path.dirname(exe_path)
                
                # 检查是否是临时目录
                if 'temp' in app_dir.lower() or 'tmp' in app_dir.lower():
                    if len(sys.argv) > 0:
                        real_exe_path = os.path.abspath(sys.argv[0])
                        app_dir = os.path.dirname(real_exe_path)
                        
                        if 'temp' in app_dir.lower() or 'tmp' in app_dir.lower():
                            app_dir = os.getcwd()
            else:
                # 脚本模式运行
                app_dir = os.path.dirname(os.path.abspath(__file__))
                # 向上一级到项目根目录
                app_dir = os.path.dirname(app_dir)
            
            return app_dir
        except Exception:
            return os.getcwd()
