"""
照片自动整理工具 - 命令行版本

按拍摄日期整理照片文件到 YYYYMMDD 子目录。
"""

import argparse
import sys

from core import AppConfig, PhotoOrganizer


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='按拍摄日期自动整理照片文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                          使用 config.ini 配置运行
  %(prog)s --source D:\\照片          指定源目录
  %(prog)s --dry-run                预览模式，不实际复制文件
  %(prog)s --log-file run.log       记录操作日志到文件
        """
    )
    
    parser.add_argument(
        '--source',
        help='照片源目录路径'
    )
    
    parser.add_argument(
        '--output',
        help='整理后输出目录路径'
    )
    
    parser.add_argument(
        '--start-date',
        help='开始日期（YYYYMMDD 或 YYYY-MM-DD）'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，只显示将要处理的文件，不实际复制'
    )
    
    parser.add_argument(
        '--log-file',
        help='操作日志文件路径'
    )
    
    parser.add_argument(
        '--config',
        default='config.ini',
        help='配置文件路径（默认: config.ini）'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 从配置文件加载
    config = AppConfig.from_ini(args.config)
    
    # 命令行参数覆盖配置文件
    if args.source:
        config.source_path = args.source
    if args.output:
        config.output_path = args.output
    if args.start_date:
        config.start_date = args.start_date
    
    config.dry_run = args.dry_run
    config.log_file = args.log_file
    
    # 验证配置
    errors = config.validate()
    if errors:
        print("配置错误:")
        for error in errors:
            print(f"  - {error}")
        print("\n使用 --help 查看帮助信息")
        sys.exit(1)
    
    # 显示配置信息
    print("=" * 40)
    print("照片自动整理工具")
    print("-" * 40)
    print(f"源目录:   {config.source_path}")
    print(f"输出目录: {config.output_path}")
    print(f"开始日期: {config.start_date}")
    
    if config.dry_run:
        print("运行模式: 预览模式（不复制文件）")
    
    print("=" * 40)
    print()
    
    # 确认继续（非 dry-run 模式）
    if not config.dry_run:
        try:
            response = input("是否开始整理？(y/n): ")
            if response.lower() != 'y':
                print("已取消操作。")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\n已取消操作。")
            sys.exit(0)
    
    # 进度回调函数
    last_percent = [-1]  # 使用列表以便在闭包中修改
    
    def progress_callback(current: int, total: int, filename: str) -> None:
        """显示处理进度"""
        if total == 0:
            return
        
        percent = int(current * 100 / total)
        # 每 5% 或第一个/最后一个文件时显示
        if percent != last_percent[0] and (percent % 5 == 0 or current == 1 or current == total):
            last_percent[0] = percent
            # 截断过长的文件名
            display_name = filename if len(filename) <= 30 else filename[:27] + "..."
            print(f"\r进度: [{percent:3d}%] {current}/{total} - {display_name}", end="", flush=True)
    
    # 执行整理
    organizer = PhotoOrganizer(config, callback=progress_callback)
    result = organizer.organize()
    
    # 换行（进度条结束后）
    print()
    
    # 返回退出码
    if result.failed_files > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
