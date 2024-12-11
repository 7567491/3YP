import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# API相关配置
API_KEY = os.getenv("KIMI_API_KEY")
API_BASE = os.getenv("KIMI_API_BASE")
DEFAULT_MODEL = os.getenv("KIMI_DEFAULT_MODEL")

# 数据相关路径
DATA_DIR = BASE_DIR / "data"
ANNUAL_REPORTS_DIR = DATA_DIR / "annual"
DB_PATH = DATA_DIR / "data.db"

# PDF处理相关配置
PDF_CHUNK_SIZE = 4000  # 每个文本块的最大字符数
MAX_RETRIES = 3  # API调用最大重试次数

# LLM相关配置
LLM_MODEL = DEFAULT_MODEL
LLM_TEMPERATURE = 0.1

# 确保必要的目录存在
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "financial_parser.log"

# 确保必要的目录存在
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
ANNUAL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)