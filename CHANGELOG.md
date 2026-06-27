# Changelog

本文件记录 photo-autocopy 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
