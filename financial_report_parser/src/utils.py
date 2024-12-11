import logging
import colorama
from pathlib import Path
from colorama import Fore, Style
import sys
import time
import json
from typing import Dict, Any, Generator

# 初始化colorama
colorama.init()

class ColoredFormatter(logging.Formatter):
    """自定义的彩色日志格式器"""
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

class ProgressBar:
    """进度条实现"""
    def __init__(self, total: int, prefix: str = '', suffix: str = '', decimals: int = 1, length: int = 50, fill: str = '█'):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.iteration = 0

    def print(self, iteration: int = None):
        if iteration is not None:
            self.iteration = iteration
        else:
            self.iteration += 1
            
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.iteration / float(self.total)))
        filled_length = int(self.length * self.iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        print(f'\r{self.prefix} |{bar}| {percent}% {self.suffix}', end='\r')
        if self.iteration == self.total:
            print()

class ProcessTracker:
    """处理进度跟踪器"""
    def __init__(self, save_path: Path):
        self.save_path = save_path
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """加载处理状态"""
        if self.save_path.exists():
            with open(self.save_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'current_chunk': 0,
            'processed_chunks': [],
            'results': {}
        }

    def save_state(self):
        """保存处理状态"""
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def is_chunk_processed(self, chunk_index: int) -> bool:
        """检查文本块是否已处理"""
        return chunk_index in self.state['processed_chunks']

    def save_chunk_result(self, chunk_index: int, result: Dict[str, Any]):
        """保存文本块处理结果"""
        self.state['current_chunk'] = chunk_index
        self.state['processed_chunks'].append(chunk_index)
        self.state['results'].update(result)
        self.save_state()

def stream_output(text: str, delay: float = 0.01, end: str = '\n'):
    """流式输出文本"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(end)
    sys.stdout.flush()

def setup_logging(log_file: Path = None):
    """设置日志"""
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    file_handler = logging.FileHandler(log_file or 'financial_parser.log', encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
