import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, smtp_config):
        self.smtp_config = smtp_config
    
    def send_audit_alert(self, record, recipients):
        """发送审计结果告警邮件"""
        record_id, verdict, created_at, url, reason = record
        
        subject = f"【审计告警】发现{verdict}的审计记录 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: {'#d32f2f' if verdict == '不合格' else '#ff9800'};">
                    🚨 审计结果告警通知
                </h2>
                
                <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid {'#d32f2f' if verdict == '不合格' else '#ff9800'};">
                    <h3>告警详情</h3>
                    <ul>
                        <li><strong>记录ID：</strong>{record_id}</li>
                        <li><strong>审计结果：</strong><span style="color: {'#d32f2f' if verdict == '不合格' else '#ff9800'}; font-weight: bold;">{verdict}</span></li>
                        <li><strong>发现时间：</strong>{created_at}</li>
                        <li><strong>URL：</strong>{url or '无'}</li>
                        <li><strong>原因：</strong>{reason or '无'}</li>
                    </ul>
                </div>
                
                <div style="margin-top: 20px; font-size: 12px; color: #666;">
                    <p>此邮件由审计告警系统自动发送，请勿回复。</p>
                    <p>发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(subject, html_content, recipients)
    
    def send_image_alert(self, record, recipients):
        """发送图像审计告警邮件"""
        record_id, audit_result, created_at, ip_address, mac_address, reasons = record
        
        subject = f"【图像审计告警】发现{audit_result}的图像审计记录 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: {'#d32f2f' if audit_result == '不合格' else '#ff9800'};">
                    🖼️ 图像审计告警通知
                </h2>
                
                <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid {'#d32f2f' if audit_result == '不合格' else '#ff9800'};">
                    <h3>告警详情</h3>
                    <ul>
                        <li><strong>记录ID：</strong>{record_id}</li>
                        <li><strong>审计结果：</strong><span style="color: {'#d32f2f' if audit_result == '不合格' else '#ff9800'}; font-weight: bold;">{audit_result}</span></li>
                        <li><strong>发现时间：</strong>{created_at}</li>
                        <li><strong>IP地址：</strong>{ip_address}</li>
                        <li><strong>MAC地址：</strong>{mac_address}</li>
                        <li><strong>原因：</strong>{reasons or '无'}</li>
                    </ul>
                </div>
                
                <div style="margin-top: 20px; font-size: 12px; color: #666;">
                    <p>此邮件由图像审计告警系统自动发送，请勿回复。</p>
                    <p>发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(subject, html_content, recipients)
    
    def _send_email(self, subject, content, recipients):
        """发送邮件"""
        if not recipients:
            logger.warning("没有配置收件人")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = Header(subject, 'utf-8')
            
            msg.attach(MIMEText(content, 'html', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False