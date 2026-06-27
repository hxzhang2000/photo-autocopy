# 照片自动整理工具

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/hxzhang2000/photo-autocopy/releases)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](#许可证)

按照拍摄日期自动整理照片文件的 Python 工具集。提供命令行和图形界面两个版本，满足不同使用场景。

## 目录

- [功能特点](#功能特点)
- [快速开始](#快速开始)
- [安装方式](#安装方式)
- [使用方法](#使用方法)
- [配置说明](#配置说明)
- [支持的照片格式](#支持的照片格式)
- [工作原理](#工作原理)
- [故障排除](#故障排除)
- [更新日志](#更新日志)
- [许可证](#许可证)

## 功能特点

### 核心功能
- 📁 从指定源路径递归扫描照片文件
- 📅 提取 EXIF 拍摄日期（`DateTimeOriginal` → `DateTimeDigitized` → `Image DateTime` → 文件修改时间）
- 📂 按 `YYYYMMDD` 格式创建日期子目录并归档照片
- 🔒 自动处理文件名冲突（追加 `_1`, `_2` 等后缀）
- ⏱️ 仅处理指定日期之后拍摄的照片
- 🔢 **每日最少数量** — 低于指定数量的日期将被跳过
- 🧪 **干运行模式** — 预览将要处理的文件，不实际复制
- 🔗 **RAW+JPEG 配对** — 自动识别同一拍摄的 RAW 和 JPEG 文件，确保它们在同一目录

### 命令行版本 (`photo_autocopy.py`)
- 支持 `--source`, `--output`, `--start-date` 命令行参数
- `--dry-run` 预览模式，安全验证
- `--log-file` 记录详细操作日志到文件
- `tqdm` 进度条实时显示处理进度和速度
- 参数优先级：命令行 > 配置文件 > 默认值
- 适合批量处理和自动化脚本调用

### 图形界面版本 (`photo_autocopy_gui.py`)
- 直观的 tkinter 界面，操作简便
- 文件选择对话框，无需手动编辑配置
- 实时日志输出和进度显示
- 后台线程处理，界面保持响应
- 支持停止按钮中断处理

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/hxzhang2000/photo-autocopy.git
cd photo-autocopy

# 2. 安装依赖
pip install -r requirements.txt

# 3. 编辑配置（命令行版本）
# 修改 config.ini 中的 source_path 和 output_path

# 4. 运行
python photo_autocopy.py      # 命令行版本
python photo_autocopy_gui.py  # 图形界面版本
```

## 安装方式

### 方式一：从源码运行

**环境要求：** Python 3.7+

```bash
pip install -r requirements.txt
```

依赖项：
- `exifread` >= 3.0.0 — 读取 EXIF 元数据
- `tqdm` >= 4.60.0 — 进度条显示
- `tkinter` — GUI 界面（Python 标准库，无需额外安装）

### 方式二：使用预编译程序

直接下载 `photo_autocopy.exe`，无需安装 Python 环境。

> ⚠️ 预编译版本仅包含命令行功能。如需图形界面，请从源码运行。

## 使用方法

### 命令行版本

1. **配置参数** — 编辑 `config.ini`：

   ```ini
   [Paths]
   source_path = D:\照片\原始目录
   output_path = D:\照片\整理后

   [Settings]
   start_date = 20250101
   min_photos_per_day = 1
   ```

2. **运行程序**：

   ```bash
   # 使用配置文件运行
   python photo_autocopy.py

   # 命令行参数覆盖配置
   python photo_autocopy.py --source D:\照片 --output D:\整理后 --start-date 20250101

   # 预览模式（不实际复制）
   python photo_autocopy.py --dry-run

   # 记录操作日志
   python photo_autocopy.py --log-file run.log

   # 查看所有参数
   python photo_autocopy.py --help
   ```

3. 程序将自动扫描、提取日期、复制文件到对应日期目录。

### 图形界面版本

1. **启动程序**：

   ```bash
   python photo_autocopy_gui.py
   ```

2. 在界面上设置源路径、输出路径和开始日期
3. 点击 **"开始整理照片"** 按钮
4. 查看实时进度和处理日志

## 配置说明

### 配置文件 (`config.ini`)

| 参数 | 说明 | 格式要求 |
|------|------|----------|
| `source_path` | 照片源文件夹路径 | 有效目录路径 |
| `output_path` | 整理后输出路径 | 有效目录路径（自动创建） |
| `start_date` | 开始日期阈值 | `YYYYMMDD`（推荐）或 `YYYY-MM-DD` |
| `min_photos_per_day` | 每日最少照片数量 | 正整数（默认: 1，即不过滤） |

> 💡 **提示**：日期格式推荐使用 `YYYYMMDD`，使用 `YYYY-MM-DD` 时程序会显示警告。

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--source SOURCE` | 照片源目录（覆盖配置文件） |
| `--output OUTPUT` | 输出目录（覆盖配置文件） |
| `--start-date DATE` | 开始日期（覆盖配置文件） |
| `--min-photos NUM` | 每日最少照片数量（覆盖配置文件） |
| `--dry-run` | 预览模式，只显示将要处理的文件 |
| `--log-file FILE` | 记录操作日志到指定文件 |
| `--config FILE` | 指定配置文件路径（默认: `config.ini`） |
| `--help` | 显示帮助信息 |

**参数优先级**：命令行参数 > 配置文件 > 默认值

## 支持的照片格式

| 类型 | 格式 | 扩展名 |
|------|------|--------|
| 常见格式 | JPEG | `.jpg`, `.jpeg` |
| | PNG | `.png` |
| | GIF | `.gif` |
| | BMP | `.bmp` |
| | TIFF | `.tiff` |
| Apple | HEIC/HEIF | `.heic`, `.heif` |
| RAW 格式 | Generic RAW | `.raw` |
| | Nikon | `.nef` |
| | Sony | `.arw` |
| | Canon | `.cr2`, `.cr3` |
| | Adobe DNG | `.dng` |

## 工作原理

```
源目录照片 → 读取 EXIF 日期 → 过滤日期范围 → 创建日期目录 → 复制文件
                                    ↓
                            无 EXIF 则用文件修改时间
```

1. 递归遍历源目录所有文件
2. 筛选支持的照片格式
3. 提取拍摄日期（优先 EXIF，降级用文件 mtime）
4. 跳过早于 `start_date` 的照片
5. 复制到 `output_path/YYYYMMDD/` 目录
6. 同名文件自动添加序号后缀

### RAW+JPEG 配对

工具会自动识别同一拍摄的 RAW 和 JPEG 文件，确保它们始终在同一目录：

**匹配规则：**
1. **文件名匹配** — 相同基础名称（如 `IMG_1234.nef` 和 `IMG_1234.jpg`）
2. **时间戳匹配** — 拍摄时间差异在 5 秒以内

**示例：**
```
源文件:
  IMG_1234.jpg   (2026-01-15 10:30:00)
  IMG_1234.nef   (2026-01-15 10:30:00)
  IMG_1235.jpg   (2026-01-15 10:31:00)
  IMG_1235.arw   (2026-01-15 10:31:01)

输出:
  20260115/
    IMG_1234.jpg
    IMG_1234.nef
    IMG_1235.jpg
    IMG_1235.arw
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError: exifread` | 运行 `pip install -r requirements.txt` |
| 源路径不存在 | 检查 `config.ini` 中的 `source_path` 配置 |
| 日期格式错误 | 使用 `YYYYMMDD` 格式（如 `20250101`） |
| 文件复制失败 | 检查源路径读取权限和输出路径写入权限 |
| 照片未被处理 | 确认文件扩展名在支持列表中 |

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**作者**: hxzhang2000 | **仓库**: [github.com/hxzhang2000/photo-autocopy](https://github.com/hxzhang2000/photo-autocopy)
