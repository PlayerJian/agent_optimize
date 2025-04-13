import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name=None, level=logging.INFO, log_file=None, max_size=10*1024*1024, backup_count=5):
    """
    配置并返回一个日志记录器
    
    参数:
        name (str): 日志记录器名称，默认为None（使用root logger）
        level (int): 日志级别，默认为INFO
        log_file (str): 日志文件路径，默认为None（仅控制台输出）
        max_size (int): 日志文件最大大小（字节），默认为10MB
        backup_count (int): 保留的日志文件数量，默认为5
        
    返回:
        logging.Logger: 配置好的日志记录器
    """
    # 获取日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除已有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 创建滚动文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger