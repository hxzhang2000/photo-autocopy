import os
import shutil
import datetime
import exifread
import threading
import configparser
import tkinter as tk
import os
import sys
from tkinter import filedialog, messagebox, ttk
from tqdm import tqdm

class PhotoAutocopyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("照片自动整理工具")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 设置中文字体
        self.default_font = ('Microsoft YaHei UI', 10)
        self.title_font = ('Microsoft YaHei UI', 12, 'bold')
        
        # 初始化基本变量
        self.source_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.start_date = tk.StringVar()
        self.is_processing = False
        self.process_thread = None
        
        # 先创建界面，确保log_text等UI元素先被初始化
        self.create_widgets()
        
        # 再读取配置文件
        self.load_config()
        
    def get_app_directory(self):
        """获取程序所在目录，支持不同的打包工具"""
        try:
            # 首先尝试获取真实的exe路径
            if hasattr(sys, '_MEIPASS') or getattr(sys, 'frozen', False):
                # 处理打包后的情况
                # 方法1: 使用os.path.realpath获取真实路径
                exe_path = os.path.realpath(sys.executable)
                app_dir = os.path.dirname(exe_path)
                
                # 检查是否是临时目录
                if 'temp' in app_dir.lower() or 'tmp' in app_dir.lower():
                    # 尝试方法2: 从命令行参数获取
                    if len(sys.argv) > 0:
                        real_exe_path = os.path.abspath(sys.argv[0])
                        app_dir = os.path.dirname(real_exe_path)
                        
                        # 再次检查是否是临时目录
                        if 'temp' in app_dir.lower() or 'tmp' in app_dir.lower():
                            # 尝试方法3: 使用当前工作目录
                            app_dir = os.getcwd()
            else:
                # 当程序以脚本形式运行时
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            return app_dir
        except Exception as e:
            # 发生任何错误时，回退到当前工作目录
            return os.getcwd()
            
    def load_config(self):
        """从配置文件中读取参数"""
        config = configparser.ConfigParser()
        
        # 获取程序所在目录
        app_dir = self.get_app_directory()
        config_path = os.path.join(app_dir, 'config.ini')
        
        # 默认值
        default_source = r"D:\hxzhang\照片\phone-sync"
        default_output = r"D:\hxzhang\照片\phone-sync-organized"
        default_date = "2025-10-05"
        
        # 读取配置文件
        if os.path.exists(config_path):
            try:
                config.read(config_path, encoding='utf-8')
                
                # 读取Paths部分的参数
                if 'Paths' in config:
                    source_path = config['Paths'].get('source_path', default_source)
                    output_path = config['Paths'].get('output_path', default_output)
                    self.source_path.set(source_path)
                    self.output_path.set(output_path)
                
                # 读取Settings部分的参数
                if 'Settings' in config:
                    start_date = config['Settings'].get('start_date', default_date)
                    self.start_date.set(start_date)
                
                # 记录日志（在GUI创建后会显示）
                self.log_loaded_config = "已从配置文件加载参数"
                
            except Exception as e:
                # 如果读取配置文件失败，使用默认值
                self.source_path.set(default_source)
                self.output_path.set(default_output)
                self.start_date.set(default_date)
                self.log_loaded_config = f"读取配置文件失败: {e}，使用默认参数"
        else:
            # 如果配置文件不存在，使用默认值
            self.source_path.set(default_source)
            self.output_path.set(default_output)
            self.start_date.set(default_date)
            self.log_loaded_config = "配置文件不存在，使用默认参数"
            # 尝试创建配置文件
            self.save_config(default_source, default_output, default_date)
    
    def save_config(self, source_path, output_path, start_date):
        """将参数保存到配置文件"""
        try:
            config = configparser.ConfigParser()
            
            # 获取程序所在目录
            app_dir = self.get_app_directory()
            config_path = os.path.join(app_dir, 'config.ini')
            
            # 添加Paths部分
            config['Paths'] = {
                'source_path': source_path,
                'output_path': output_path
            }
            
            # 添加Settings部分
            config['Settings'] = {
                'start_date': start_date
            }
            
            # 写入配置文件
            with open(config_path, 'w', encoding='utf-8') as config_file:
                config.write(config_file)
            
            self.log_message(f"已保存配置到 {config_path}")
            
        except Exception as e:
            self.log_message(f"保存配置文件失败: {e}")
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=(20, 20, 20, 20))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题标签
        title_label = ttk.Label(main_frame, text="照片自动整理工具", font=self.title_font)
        title_label.pack(pady=(0, 20))
        
        # 配置区域框架
        config_frame = ttk.LabelFrame(main_frame, text="配置参数", padding=(10, 10, 10, 10))
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 源路径选择
        ttk.Label(config_frame, text="源路径:", font=self.default_font).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.source_path, width=50, font=self.default_font).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(config_frame, text="浏览...", command=self.browse_source).grid(row=0, column=2, padx=5, pady=5)
        
        # 输出路径选择
        ttk.Label(config_frame, text="输出路径:", font=self.default_font).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.output_path, width=50, font=self.default_font).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(config_frame, text="浏览...", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        # 开始日期选择
        ttk.Label(config_frame, text="开始日期:", font=self.default_font).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.start_date, width=20, font=self.default_font).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(config_frame, text="(格式: YYYY-MM-DD 或 YYYYMMDD)", font=self.default_font).grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # 开始按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        self.start_button = ttk.Button(button_frame, text="开始整理照片", command=self.start_processing, width=20)
        self.start_button.pack(pady=10)
        
        # 进度条区域
        progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding=(10, 10, 10, 10))
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="准备就绪", font=self.default_font)
        self.progress_label.pack(pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding=(10, 10, 10, 10))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        log_scrollbar = ttk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建文本框用于显示日志
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, yscrollcommand=log_scrollbar.set, height=10, font=self.default_font)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        
        # 使文本框不可编辑
        self.log_text.config(state=tk.DISABLED)
        
        # 显示配置加载信息
        if hasattr(self, 'log_loaded_config'):
            self.log_message(self.log_loaded_config)
        
    def browse_source(self):
        directory = filedialog.askdirectory(title="选择照片源目录")
        if directory:
            self.source_path.set(directory)
    
    def browse_output(self):
        directory = filedialog.askdirectory(title="选择照片输出目录")
        if directory:
            self.output_path.set(directory)
    
    def log_message(self, message):
        """在日志文本框中显示消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # 滚动到最新消息
        self.log_text.config(state=tk.DISABLED)
    
    def update_progress(self, value, message=""):
        """更新进度条和进度标签"""
        self.progress_var.set(value)
        if message:
            self.progress_label.config(text=message)
        self.root.update_idletasks()
    
    def start_processing(self):
        """开始处理照片（在新线程中执行）"""
        if self.is_processing:
            messagebox.showwarning("警告", "照片整理任务正在执行中，请等待完成！")
            return
        
        # 获取配置参数
        source = self.source_path.get()
        output = self.output_path.get()
        start_date = self.start_date.get()
        
        # 验证参数
        if not source or not os.path.exists(source):
            messagebox.showerror("错误", "源路径不存在，请选择有效的源路径！")
            return
        
        if not output:
            messagebox.showerror("错误", "请选择有效的输出路径！")
            return
        
        # 验证日期格式
        try:
            # 尝试解析日期格式
            if '-' in start_date:
                datetime.datetime.strptime(start_date, '%Y-%m-%d')
            else:
                datetime.datetime.strptime(start_date, '%Y%m%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式无效，请使用YYYY-MM-DD或YYYYMMDD格式！")
            return
        
        # 确保输出目录存在
        if not os.path.exists(output):
            try:
                os.makedirs(output)
                self.log_message(f"创建输出目录: {output}")
            except Exception as e:
                messagebox.showerror("错误", f"创建输出目录失败: {e}")
                return
        
        # 保存配置参数
        self.save_config(source, output, start_date)
        
        # 禁用开始按钮
        self.start_button.config(state=tk.DISABLED)
        self.is_processing = True
        
        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 在新线程中执行处理任务
        self.process_thread = threading.Thread(
            target=self.organize_photos_by_date,
            args=(source, output, start_date)
        )
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def get_photo_creation_date(self, file_path):
        """从照片文件中提取拍摄日期"""
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                # 尝试从EXIF信息中获取拍摄日期
                if 'EXIF DateTimeOriginal' in tags:
                    date_str = str(tags['EXIF DateTimeOriginal'])
                    # 将EXIF日期格式(YYYY:MM:DD HH:MM:SS)转换为YYYYMMDD
                    return date_str.split(' ')[0].replace(':', '')
                elif 'Image DateTime' in tags:
                    date_str = str(tags['Image DateTime'])
                    return date_str.split(' ')[0].replace(':', '')
                else:
                    # 如果没有EXIF日期，则返回文件的修改日期
                    mtime = os.path.getmtime(file_path)
                    return datetime.datetime.fromtimestamp(mtime).strftime('%Y%m%d')
        except Exception as e:
            self.log_message(f"无法提取文件 {os.path.basename(file_path)} 的日期信息: {e}")
            return None
    
    def is_photo_file(self, filename):
        """判断文件是否为照片文件"""
        photo_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.nef']
        ext = os.path.splitext(filename)[1].lower()
        return ext in photo_extensions
    
    def organize_photos_by_date(self, source_path, output_path, start_date_str):
        """按照拍摄日期整理照片"""
        try:
            # 记录开始时间
            start_time = datetime.datetime.now()
            self.log_message(f"===== 开始照片整理任务 =====")
            self.log_message(f"源路径: {source_path}")
            self.log_message(f"输出路径: {output_path}")
            self.log_message(f"开始日期: {start_date_str}")
            
            # 将开始日期转换为datetime对象用于比较
            try:
                if '-' in start_date_str:
                    start_date_obj = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
                    self.log_message(f"注意: 使用了YYYY-MM-DD格式，建议修改为YYYYMMDD格式")
                else:
                    start_date_obj = datetime.datetime.strptime(start_date_str, '%Y%m%d')
            except ValueError:
                self.log_message(f"错误: 日期格式无效: {start_date_str}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"日期格式无效: {start_date_str}"))
                self.root.after(0, self.finish_processing)
                return
            
            # 收集所有需要处理的文件
            self.log_message("正在收集所有文件...")
            all_files = []
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    all_files.append(os.path.join(root, file))
            
            total_files = len(all_files)
            processed_files = 0
            skipped_files = 0
            
            self.log_message(f"共发现 {total_files} 个文件")
            
            # 遍历处理文件
            for i, file_path in enumerate(all_files):
                file = os.path.basename(file_path)
                
                # 更新进度
                progress_percent = (i + 1) / total_files * 100
                self.root.after(0, lambda p=progress_percent, f=file: self.update_progress(p, f"正在处理: {f}"))
                
                # 只处理照片文件
                if not self.is_photo_file(file):
                    skipped_files += 1
                    continue
                
                # 获取照片的拍摄日期
                photo_date = self.get_photo_creation_date(file_path)
                if not photo_date:
                    skipped_files += 1
                    continue
                
                # 检查日期是否在开始整理日期之后
                try:
                    photo_date_obj = datetime.datetime.strptime(photo_date, '%Y%m%d')
                    if photo_date_obj < start_date_obj:
                        skipped_files += 1
                        continue
                except ValueError:
                    self.log_message(f"无效的日期格式: {photo_date}")
                    skipped_files += 1
                    continue
                
                # 创建对应的日期子目录
                date_dir = os.path.join(output_path, photo_date)
                if not os.path.exists(date_dir):
                    try:
                        os.makedirs(date_dir)
                        self.log_message(f"创建日期目录: {photo_date}")
                    except Exception as e:
                        self.log_message(f"创建目录失败 {date_dir}: {e}")
                        skipped_files += 1
                        continue
                
                # 拷贝照片到对应的日期子目录
                destination_path = os.path.join(date_dir, file)
                
                # 如果目标文件已存在，则添加编号避免覆盖
                if os.path.exists(destination_path):
                    base_name, ext = os.path.splitext(file)
                    counter = 1
                    while os.path.exists(os.path.join(date_dir, f"{base_name}_{counter}{ext}")):
                        counter += 1
                    destination_path = os.path.join(date_dir, f"{base_name}_{counter}{ext}")
                
                try:
                    shutil.copy2(file_path, destination_path)
                    processed_files += 1
                except Exception as e:
                    self.log_message(f"拷贝文件 {file} 失败: {e}")
                    skipped_files += 1
            
            # 计算耗时
            end_time = datetime.datetime.now()
            elapsed_time = end_time - start_time
            
            # 完成处理
            self.log_message(f"===== 照片整理完成 =====")
            self.log_message(f"共处理 {total_files} 个文件")
            self.log_message(f"成功拷贝 {processed_files} 个照片文件")
            self.log_message(f"跳过 {skipped_files} 个文件")
            self.log_message(f"总耗时: {elapsed_time}")
            
            # 显示完成消息
            self.root.after(0, lambda: messagebox.showinfo("完成", f"照片整理完成！\n共处理 {total_files} 个文件\n成功拷贝 {processed_files} 个照片文件\n跳过 {skipped_files} 个文件"))
        except Exception as e:
            self.log_message(f"处理过程中发生错误: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理过程中发生错误: {e}"))
        finally:
            # 完成处理，重置状态
            self.root.after(0, self.finish_processing)
    
    def finish_processing(self):
        """完成处理后重置UI状态"""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.update_progress(100, "处理完成")
        self.log_message("任务已完成，可以开始新的整理任务。")

if __name__ == "__main__":
    # 检查必要的库是否安装
    try:
        import exifread
    except ImportError:
        import sys
        print("错误: 未安装exifread库。请先运行 'pip install exifread' 安装该库。")
        input("按Enter键退出...")
        sys.exit(1)
    
    try:
        from tqdm import tqdm
    except ImportError:
        import sys
        print("错误: 未安装tqdm库。请先运行 'pip install tqdm' 安装该库。")
        input("按Enter键退出...")
        sys.exit(1)
    
    # 创建并运行GUI应用
    root = tk.Tk()
    app = PhotoAutocopyGUI(root)
    root.mainloop()