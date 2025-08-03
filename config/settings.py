import os
from dotenv import load_dotenv

load_dotenv()

# API配置
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'audit_alert.log')

# 配置缓存时间（秒）
CONFIG_CACHE_TIME = 300  # 5分钟