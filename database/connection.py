import os
import psycopg
from psycopg.rows import dict_row
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection_string = (
            f"host={os.getenv('DB_HOST')} "
            f"port={os.getenv('DB_PORT')} "
            f"dbname={os.getenv('DB_NAME')} "
            f"user={os.getenv('DB_USER')} "
            f"password={os.getenv('DB_PASSWORD')}"
        )
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = psycopg.connect(self.connection_string, row_factory=dict_row)
            return conn
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return None
    
    def execute_query(self, query, params=None):
        """执行查询"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

# 全局数据库实例
db = Database()