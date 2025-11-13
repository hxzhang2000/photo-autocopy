import os
import shutil
import datetime
import exifread
import configparser
from tqdm import tqdm

# 默认配置值（在配置文件读取失败时使用）
DEFAULT_SOURCE_PATH = r"D:\hxzhang\照片\phone-sync"
DEFAULT_OUTPUT_PATH = r"D:\hxzhang\照片\phone-sync-organized"
DEFAULT_START_DATE = "2025-10-05"

# 全局变量，将在load_config函数中初始化
SOURCE_PATH = None
OUTPUT_PATH = None
START_DATE = None


def load_config(config_file='config.ini'):
    """
    从配置文件中加载参数
    :param config_file: 配置文件路径
    :return: 配置是否成功加载
    """
    global SOURCE_PATH, OUTPUT_PATH, START_DATE
    
    # 创建配置解析器
    config = configparser.ConfigParser()
    
    try:
        # 检查配置文件是否存在
        if not os.path.exists(config_file):
            print(f"警告: 配置文件 {config_file} 不存在，将使用默认值并创建示例配置文件。")
            create_default_config(config_file)
            return False
        
        # 读取配置文件
        config.read(config_file, encoding='utf-8')
        
        # 加载路径配置
        if 'Paths' in config:
            SOURCE_PATH = config['Paths'].get('source_path', DEFAULT_SOURCE_PATH)
            OUTPUT_PATH = config['Paths'].get('output_path', DEFAULT_OUTPUT_PATH)
        else:
            print("警告: 配置文件中未找到Paths部分，将使用默认值。")
            SOURCE_PATH = DEFAULT_SOURCE_PATH
            OUTPUT_PATH = DEFAULT_OUTPUT_PATH
        
        # 加载设置配置
        if 'Settings' in config:
            START_DATE = config['Settings'].get('start_date', DEFAULT_START_DATE)
        else:
            print("警告: 配置文件中未找到Settings部分，将使用默认值。")
            START_DATE = DEFAULT_START_DATE
        
        # 验证路径是否存在
        if not os.path.exists(SOURCE_PATH):
            print(f"警告: 源路径 {SOURCE_PATH} 不存在，请检查配置文件。")
        
        # 确保输出路径存在
        if not os.path.exists(OUTPUT_PATH):
            print(f"信息: 输出路径 {OUTPUT_PATH} 不存在，将在运行时创建。")
        
        print(f"成功加载配置文件: {config_file}")
        print(f"源路径: {SOURCE_PATH}")
        print(f"输出路径: {OUTPUT_PATH}")
        print(f"开始日期: {START_DATE}")
        
        return True
        
    except Exception as e:
        print(f"错误: 读取配置文件时发生错误: {e}")
        print("将使用默认配置值。")
        # 使用默认值
        SOURCE_PATH = DEFAULT_SOURCE_PATH
        OUTPUT_PATH = DEFAULT_OUTPUT_PATH
        START_DATE = DEFAULT_START_DATE
        return False


def create_default_config(config_file='config.ini'):
    """
    创建默认配置文件
    :param config_file: 配置文件路径
    """
    config = configparser.ConfigParser()
    
    # 添加路径配置
    config['Paths'] = {
        'source_path': DEFAULT_SOURCE_PATH,
        'output_path': DEFAULT_OUTPUT_PATH
    }
    
    # 添加设置配置
    config['Settings'] = {
        'start_date': DEFAULT_START_DATE
    }
    
    # 写入配置文件
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        print(f"已创建默认配置文件: {config_file}")
    except Exception as e:
        print(f"错误: 创建配置文件失败: {e}")


def get_photo_creation_date(file_path):
    """
    从照片文件中提取拍摄日期
    :param file_path: 照片文件路径
    :return: 拍摄日期（YYYYMMDD格式的字符串），如果无法提取则返回None
    """
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
        print(f"无法提取文件 {file_path} 的日期信息: {e}")
        return None


def is_photo_file(filename):
    """
    判断文件是否为照片文件
    :param filename: 文件名
    :return: 是否为照片文件
    """
    photo_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.nef']
    ext = os.path.splitext(filename)[1].lower()
    return ext in photo_extensions


def organize_photos_by_date():
    """
    按照拍摄日期整理照片
    """
    # 确保输出目录存在
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
        print(f"创建输出目录: {OUTPUT_PATH}")
    
    # 将开始日期转换为datetime对象用于比较
    try:
        start_date_obj = datetime.datetime.strptime(START_DATE, '%Y%m%d')
    except ValueError:
        # 兼容原有的YYYY-MM-DD格式
        start_date_obj = datetime.datetime.strptime(START_DATE, '%Y-%m-%d')
        print(f"注意: 检测到开始日期使用了YYYY-MM-DD格式，建议修改为YYYYMMDD格式")
    
    # 收集所有需要处理的文件
    all_files = []
    for root, dirs, files in os.walk(SOURCE_PATH):
        for file in files:
            all_files.append(os.path.join(root, file))
    
    total_files = len(all_files)
    processed_files = 0
    
    # 使用tqdm创建进度条
    with tqdm(total=total_files, desc="处理进度") as pbar:
        for file_path in all_files:
            file = os.path.basename(file_path)
            
            # 只处理照片文件
            if not is_photo_file(file):
                pbar.update(1)
                continue
            
            # 获取照片的拍摄日期
            photo_date = get_photo_creation_date(file_path)
            if not photo_date:
                pbar.update(1)
                continue
            
            # 检查日期是否在开始整理日期之后
            try:
                photo_date_obj = datetime.datetime.strptime(photo_date, '%Y%m%d')
                if photo_date_obj < start_date_obj:
                    pbar.update(1)
                    continue
            except ValueError:
                print(f"无效的日期格式: {photo_date}")
                pbar.update(1)
                continue
            
            # 创建对应的日期子目录
            date_dir = os.path.join(OUTPUT_PATH, photo_date)
            if not os.path.exists(date_dir):
                os.makedirs(date_dir)
                print(f"创建日期目录: {date_dir}")
            
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
                # 可选：在进度条描述中显示当前处理的文件
                pbar.set_postfix_str(f"正在处理: {file}")
            except Exception as e:
                print(f"拷贝文件 {file_path} 失败: {e}")
            
            pbar.update(1)
    
    print(f"照片整理完成! 共处理 {total_files} 个文件，成功拷贝 {processed_files} 个照片文件。")


def test_date_format_conversion():
    """
    测试日期格式转换功能
    """
    print("\n===== 日期格式转换测试 =====")
    
    # 测试从EXIF格式转换到YYYYMMDD格式
    exif_date = "2023:05:15 14:30:22"
    converted_date = exif_date.split(' ')[0].replace(':', '')
    print(f"EXIF格式({exif_date})转换为目录格式: {converted_date}")
    
    # 测试开始日期的兼容性
    try:
        # 测试YYYYMMDD格式
        test_date1 = "20230515"
        date_obj1 = datetime.datetime.strptime(test_date1, '%Y%m%d')
        print(f"YYYYMMDD格式({test_date1})解析成功: {date_obj1}")
        
        # 测试YYYY-MM-DD格式（兼容模式）
        test_date2 = "2023-05-15"
        date_obj2 = datetime.datetime.strptime(test_date2, '%Y-%m-%d')
        print(f"YYYY-MM-DD格式({test_date2})解析成功: {date_obj2}")
    except Exception as e:
        print(f"日期解析测试失败: {e}")
    
    print("==========================\n")


if __name__ == "__main__":
    print("===== 照片自动整理工具 =====")
    
    # 1. 加载配置文件
    print("\n1. 正在加载配置文件...")
    config_loaded = load_config()
    
    # 2. 检查必要的库是否安装
    print("\n2. 正在检查必要的库是否安装...")
    try:
        import exifread
    except ImportError:
        print("错误: 未安装exifread库。请先运行 'pip install exifread' 安装该库。")
        exit(1)
    
    try:
        from tqdm import tqdm
    except ImportError:
        print("错误: 未安装tqdm库。请先运行 'pip install tqdm' 安装该库。")
        exit(1)
    
    # 3. 运行日期格式转换测试
    print("\n3. 正在进行日期格式转换测试...")
    test_date_format_conversion()
    
    # 4. 开始整理照片
    print("\n4. 开始整理照片...")
    print(f"源路径: {SOURCE_PATH}")
    print(f"输出路径: {OUTPUT_PATH}")
    print(f"开始日期: {START_DATE}")
    
    # 确认用户是否继续
    if not config_loaded:
        response = input("\n配置文件存在问题，是否继续使用默认配置？(y/n): ")
        if response.lower() != 'y':
            print("程序已取消。")
            exit(0)
    
    # 开始执行整理任务
    print("\n开始执行整理任务...")
    organize_photos_by_date()
    print("\n===== 照片自动整理完成 =====")