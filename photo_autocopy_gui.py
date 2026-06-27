"""
照片自动整理工具 - 图形界面版本

提供直观的 GUI 界面用于按日期整理照片。
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from core import AppConfig, PhotoOrganizer, PHOTO_EXTENSIONS


class PhotoAutocopyGUI:
    """照片自动整理工具 GUI"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("照片自动整理工具")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # 字体配置
        self.default_font = ('Microsoft YaHei UI', 10)
        self.title_font = ('Microsoft YaHei UI', 12, 'bold')
        
        # 状态变量
        self.source_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.start_date = tk.StringVar()
        self.min_photos = tk.StringVar(value="1")
        self.dry_run = tk.BooleanVar(value=False)
        self.is_processing = False
        self.process_thread: Optional[threading.Thread] = None
        
        # 创建界面
        self._create_widgets()
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """从配置文件加载参数"""
        config = AppConfig.from_ini('config.ini')
        
        self.source_path.set(config.source_path)
        self.output_path.set(config.output_path)
        self.start_date.set(config.start_date)
        self.min_photos.set(str(config.min_photos_per_day))
        
        self._log("已从配置文件加载参数")
    
    def _save_config(self) -> None:
        """保存当前参数到配置文件"""
        try:
            min_photos = int(self.min_photos.get())
        except ValueError:
            min_photos = 1
        
        config = AppConfig(
            source_path=self.source_path.get(),
            output_path=self.output_path.get(),
            start_date=self.start_date.get(),
            min_photos_per_day=min_photos,
        )
        config.save_ini('config.ini')
        self._log("已保存配置到 config.ini")
    
    def _create_widgets(self) -> None:
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="照片自动整理工具", font=self.title_font)
        title_label.pack(pady=(0, 20))
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置参数", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 源路径
        ttk.Label(config_frame, text="源路径:", font=self.default_font).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(config_frame, textvariable=self.source_path, width=50, font=self.default_font).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.EW
        )
        ttk.Button(config_frame, text="浏览...", command=self._browse_source).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        # 输出路径
        ttk.Label(config_frame, text="输出路径:", font=self.default_font).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(config_frame, textvariable=self.output_path, width=50, font=self.default_font).grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.EW
        )
        ttk.Button(config_frame, text="浏览...", command=self._browse_output).grid(
            row=1, column=2, padx=5, pady=5
        )
        
        # 开始日期
        ttk.Label(config_frame, text="开始日期:", font=self.default_font).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(config_frame, textvariable=self.start_date, width=20, font=self.default_font).grid(
            row=2, column=1, padx=5, pady=5, sticky=tk.W
        )
        ttk.Label(config_frame, text="(YYYYMMDD 或 YYYY-MM-DD)", font=self.default_font).grid(
            row=2, column=2, sticky=tk.W, pady=5
        )
        
        # 每日最少照片数
        ttk.Label(config_frame, text="每日最少数量:", font=self.default_font).grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(config_frame, textvariable=self.min_photos, width=10, font=self.default_font).grid(
            row=3, column=1, padx=5, pady=5, sticky=tk.W
        )
        ttk.Label(config_frame, text="(低于此数量的日期将被跳过)", font=self.default_font).grid(
            row=3, column=2, sticky=tk.W, pady=5
        )
        
        # 配置列权重
        config_frame.columnconfigure(1, weight=1)
        
        # 选项区域
        options_frame = ttk.LabelFrame(main_frame, text="选项", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Checkbutton(
            options_frame,
            text="预览模式（不实际复制文件）",
            variable=self.dry_run,
            font=self.default_font
        ).pack(anchor=tk.W)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_button = ttk.Button(
            button_frame,
            text="开始整理照片",
            command=self._start_processing,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="停止",
            command=self._stop_processing,
            state=tk.DISABLED,
            width=10
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            length=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="准备就绪", font=self.default_font)
        self.progress_label.pack(pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            yscrollcommand=log_scrollbar.set,
            height=10,
            font=self.default_font
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        self.log_text.config(state=tk.DISABLED)
    
    def _browse_source(self) -> None:
        """选择源目录"""
        directory = filedialog.askdirectory(title="选择照片源目录")
        if directory:
            self.source_path.set(directory)
    
    def _browse_output(self) -> None:
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择照片输出目录")
        if directory:
            self.output_path.set(directory)
    
    def _log(self, message: str) -> None:
        """添加日志消息（线程安全）"""
        def _update():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.root.after(0, _update)
    
    def _update_progress(self, current: int, total: int, filename: str) -> None:
        """更新进度（线程安全）"""
        def _update():
            percent = (current / total * 100) if total > 0 else 0
            self.progress_var.set(percent)
            self.progress_label.config(text=f"正在处理: {filename} ({current}/{total})")
        
        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.root.after(0, _update)
    
    def _start_processing(self) -> None:
        """开始处理"""
        if self.is_processing:
            messagebox.showwarning("警告", "任务正在执行中！")
            return
        
        # 验证 min_photos
        try:
            min_photos = int(self.min_photos.get())
            if min_photos < 1:
                messagebox.showerror("配置错误", "每日最少数量必须大于等于 1")
                return
        except ValueError:
            messagebox.showerror("配置错误", "每日最少数量必须是整数")
            return
        
        # 创建配置
        config = AppConfig(
            source_path=self.source_path.get(),
            output_path=self.output_path.get(),
            start_date=self.start_date.get(),
            min_photos_per_day=min_photos,
            dry_run=self.dry_run.get(),
        )
        
        # 验证配置
        errors = config.validate()
        if errors:
            messagebox.showerror("配置错误", "\n".join(errors))
            return
        
        # 保存配置
        self._save_config()
        
        # 更新 UI 状态
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        
        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 显示配置信息
        self._log("=" * 40)
        self._log("开始照片整理任务")
        self._log(f"源目录: {config.source_path}")
        self._log(f"输出目录: {config.output_path}")
        self._log(f"开始日期: {config.start_date}")
        self._log(f"每日最少数量: {config.min_photos_per_day}")
        if config.dry_run:
            self._log("运行模式: 预览模式")
        self._log("=" * 40)
        
        # 启动处理线程
        self._stop_flag = False
        self.process_thread = threading.Thread(
            target=self._process_worker,
            args=(config,),
            daemon=True
        )
        self.process_thread.start()
    
    def _stop_processing(self) -> None:
        """停止处理"""
        self._stop_flag = True
        self._log("正在停止...")
    
    def _process_worker(self, config: AppConfig) -> None:
        """处理工作线程"""
        try:
            # 创建整理器，使用回调更新进度和检查停止
            organizer = PhotoOrganizer(
                config,
                callback=self._update_progress,
                stop_callback=lambda: self._stop_flag
            )
            
            # 执行整理
            result = organizer.organize()
            
            # 显示结果
            self._log("")
            self._log("整理完成！")
            
            # 显示完成对话框
            if not self._stop_flag:
                self.root.after(0, lambda: messagebox.showinfo(
                    "完成",
                    f"照片整理完成！\n\n"
                    f"总文件数: {result.total_files}\n"
                    f"成功处理: {result.processed_files}\n"
                    f"跳过文件: {result.skipped_files}\n"
                    f"失败文件: {result.failed_files}\n"
                    f"耗时: {result.elapsed_str}"
                ))
            
        except Exception as e:
            self._log(f"处理过程中发生错误: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
        
        finally:
            # 重置 UI 状态
            self.root.after(0, self._finish_processing)
    
    def _finish_processing(self) -> None:
        """完成处理后重置 UI"""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_label.config(text="处理完成")


def check_dependencies() -> bool:
    """检查依赖库是否安装"""
    missing = []
    
    try:
        import exifread
    except ImportError:
        missing.append('exifread')
    
    if missing:
        print(f"错误: 缺少以下依赖库: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        input("按 Enter 键退出...")
        return False
    
    return True


def main():
    """主函数"""
    if not check_dependencies():
        sys.exit(1)
    
    root = tk.Tk()
    app = PhotoAutocopyGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
