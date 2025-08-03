import logging
from datetime import datetime
from database.connection import db
from services.email_service import EmailService

logger = logging.getLogger(__name__)

class MonitorService:
    def __init__(self):
        self.smtp_config = None
        self.recipients = {}
        self.system_config = {}
        self.last_config_update = None
    
    def load_config(self):
        """加载配置"""
        try:
            # 加载SMTP配置
            smtp_query = "SELECT * FROM smtp_config WHERE is_active = true ORDER BY created_at DESC LIMIT 1"
            smtp_result = db.execute_query(smtp_query)
            if smtp_result:
                self.smtp_config = smtp_result[0]
            else:
                logger.error("未找到激活的SMTP配置")
                return False
            
            # 加载收件人配置
            recipients_query = "SELECT table_name, email FROM recipients_config WHERE is_active = true"
            recipients_result = db.execute_query(recipients_query)
            
            self.recipients = {}
            if recipients_result:
                for recipient in recipients_result:
                    table_name = recipient['table_name']
                    if table_name not in self.recipients:
                        self.recipients[table_name] = []
                    self.recipients[table_name].append(recipient['email'])
            
            # 加载系统配置
            config_query = "SELECT config_key, config_value FROM system_config"
            config_result = db.execute_query(config_query)
            if config_result:
                self.system_config = {config['config_key']: config['config_value'] 
                                    for config in config_result}
            
            self.last_config_update = datetime.now()
            logger.info("配置加载成功")
            return True
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            return False
    
    def is_monitor_enabled(self):
        """检查监控是否启用"""
        return self.system_config.get('monitor_enabled', 'false').lower() == 'true'
    
    def is_email_enabled(self):
        """检查邮件发送是否启用"""
        return self.system_config.get('email_enabled', 'false').lower() == 'true'
    
    def check_audit_results(self):
        """检查audit_results表"""
        if not self.is_monitor_enabled():
            return
        
        query = """
        SELECT ar.id, ar.verdict, ar.created_at, ar.url, ar.reason
        FROM audit_results ar
        LEFT JOIN email_sent_log esl ON (
            esl.table_name = 'audit_results' 
            AND esl.record_id = ar.id 
            AND esl.verdict = ar.verdict
        )
        WHERE ar.verdict IN ('不合格', '不确定') 
        AND esl.id IS NULL
        ORDER BY ar.created_at DESC
        """
        
        records = db.execute_query(query)
        if not records:
            return
        
        recipients = self.recipients.get('audit_results', [])
        if not recipients:
            logger.warning("未配置audit_results表的收件人")
            return
        
        if self.is_email_enabled() and self.smtp_config:
            email_service = EmailService(self.smtp_config)
            
            for record in records:
                if email_service.send_audit_alert(record, recipients):
                    self._log_sent_email('audit_results', record[0], record[1], recipients)
    
    def check_image_audit_results(self):
        """检查image_audit_results表"""
        if not self.is_monitor_enabled():
            return
        
        query = """
        SELECT iar.id, iar.audit_result, iar.created_at, iar.ip_address, iar.mac_address, iar.reasons
        FROM image_audit_results iar
        LEFT JOIN email_sent_log esl ON (
            esl.table_name = 'image_audit_results' 
            AND esl.record_id = iar.id 
            AND esl.verdict = iar.audit_result
        )
        WHERE iar.audit_result IN ('不合格', '不确定') 
        AND esl.id IS NULL
        ORDER BY iar.created_at DESC
        """
        
        records = db.execute_query(query)
        if not records:
            return
        
        recipients = self.recipients.get('image_audit_results', [])
        if not recipients:
            logger.warning("未配置image_audit_results表的收件人")
            return
        
        if self.is_email_enabled() and self.smtp_config:
            email_service = EmailService(self.smtp_config)
            
            for record in records:
                if email_service.send_image_alert(record, recipients):
                    self._log_sent_email('image_audit_results', record[0], record[1], recipients)
    
    def _log_sent_email(self, table_name, record_id, verdict, recipients):
        """记录已发送的邮件"""
        query = """
        INSERT INTO email_sent_log (table_name, record_id, verdict, recipients)
        VALUES (%s, %s, %s, %s)
        """
        recipients_str = ', '.join(recipients)
        db.execute_query(query, (table_name, record_id, verdict, recipients_str))
    
    def run_check(self):
        """执行检查"""
        # 重新加载配置（每5分钟）
        if (not self.last_config_update or 
            (datetime.now() - self.last_config_update).total_seconds() > 300):
            if not self.load_config():
                logger.error("配置加载失败，跳过本次检查")
                return
        
        if not self.is_monitor_enabled():
            logger.info("监控功能已禁用")
            return
        
        logger.info("开始执行审计结果检查...")
        self.check_audit_results()
        self.check_image_audit_results()
        logger.info("审计结果检查完成")