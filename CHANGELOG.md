# Changelog

本文件记录 photo-autocopy 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-06-27

### 新增

- **核心模块化架构**
  - 抽取 `core/` 包，统一管理配置、EXIF 提取和整理逻辑
  - `core/config.py` — `AppConfig` 数据类，支持 INI 加载/保存/验证
  - `core/exif.py` — 优化的 EXIF 日期提取（使用 `stop_tag` 加速）
  - `core/organizer.py` — `PhotoOrganizer` 类，支持干运行和日志

- **干运行模式**
  - CLI: `--dry-run` 参数，预览将要处理的文件
  - GUI: 预览模式复选框

- **操作日志记录**
  - CLI: `--log-file` 参数，记录详细操作日志到文件
  - 日志包含时间戳和处理详情

- **扩展格式支持**
  - 新增 HEIC/HEIF（Apple 照片）格式
  - 新增 ARW（Sony）、CR2/CR3（Canon）、DNG（Adobe）RAW 格式

- **命令行增强**
  - 使用 `argparse` 替代手动参数解析
  - 支持 `--source`, `--output`, `--start-date` 命令行参数
  - 参数优先级：命令行 > 配置文件 > 默认值

- **GUI 增强**
  - 添加"停止"按钮，支持中断处理
  - 线程安全的 UI 更新
  - 移除未使用的 tqdm 依赖

### 优化

- **EXIF 读取性能**
  - 使用 `stop_tag='EXIF DateTimeOriginal'` 只读取必要标签
  - 设置 `details=False` 跳过缩略图读取
  - 日期标签优先级：`DateTimeOriginal` → `DateTimeDigitized` → `Image DateTime`

- **代码质量**
  - 消除 CLI 和 GUI 之间的代码重复
  - 使用 `pathlib.Path` 替代部分 `os.path` 操作
  - 使用 `os.makedirs(exist_ok=True)` 简化目录创建
  - 改进异常处理，捕获具体异常类型

### 移除

- 移除 `tqdm` 依赖（CLI 改用核心模块内置进度回调）

### 已知限制

- 仅支持 Windows 平台
- 无自动化测试套件

[1.1.0]: https://github.com/hxzhang2000/photo-autocopy/releases/tag/v1.1.0

## [1.0.0] - 2026-06-27

### 新增

- **命令行版本** (`photo_autocopy.py`)
  - 从 `config.ini` 读取配置参数
  - 提取照片 EXIF 拍摄日期（`EXIF DateTimeOriginal` → `Image DateTime` → 文件修改时间）
  - 按 `YYYYMMDD` 格式创建日期子目录并复制照片
  - 自动处理文件名冲突（追加 `_1`, `_2` 等后缀）
  - 支持 `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.raw`, `.nef` 格式
  - 使用 `tqdm` 显示处理进度条
  - 配置文件不存在时自动创建默认配置

- **图形界面版本** (`photo_autocopy_gui.py`)
  - 基于 tkinter 的直观操作界面
  - 通过对话框选择源路径和输出路径
  - 实时显示处理进度和详细日志
  - 后台线程处理，不阻塞界面响应
  - 日期格式自动验证（支持 `YYYY-MM-DD` 和 `YYYYMMDD`）
  - 处理完成后自动保存配置

- **构建与分发**
  - PyInstaller 打包配置 (`PhotoAutocopy.spec`)
  - 预编译 Windows 可执行文件 (`photo_autocopy.exe`)
  - 依赖管理 (`requirements.txt`: exifread, tqdm)

- **项目文档**
  - 中文 README 说明文档
  - AGENTS.md 项目指引文件

### 已知限制

- 仅支持 Windows 平台
- CLI 和 GUI 版本核心逻辑独立实现，修改需同步两处
- 无自动化测试套件

[1.0.0]: https://github.com/hxzhang2000/photo-autocopy/releases/tag/v1.0.0
