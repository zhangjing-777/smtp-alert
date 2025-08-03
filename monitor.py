import logging
import schedule
import time
from services.monitor_service import MonitorService
from config.settings import LOG_LEVEL, LOG_FILE

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    monitor_service = MonitorService()
    
    # 初始化配置
    if not monitor_service.load_config():
        logger.error("初始化配置加载失败，程序退出")
        return
    
    # 获取检查间隔
    try:
        check_interval = int(monitor_service.system_config.get('check_interval', '5'))
    except ValueError:
        check_interval = 5
    
    # 设置定时任务
    schedule.every(check_interval).minutes.do(monitor_service.run_check)
    
    logger.info(f"审计告警监控服务启动，检查间隔: {check_interval}分钟")
    
    # 立即执行一次检查
    monitor_service.run_check()
    
    # 持续运行
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()