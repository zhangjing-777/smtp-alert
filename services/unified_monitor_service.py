
"""
统一监控服务 - 整合配置控制和进程管理
"""

import os
import time
import signal
import psutil
import subprocess
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from database.connection import db
from services.email_service import EmailService

logger = logging.getLogger(__name__)

class UnifiedMonitorService:
    def __init__(self):
        self.pid_file = "monitor.pid"
        self.log_file = "monitor.log"
        self.monitor_script = "monitor.py"
        
        # 配置缓存
        self.smtp_config = None
        self.recipients = {}
        self.system_config = {}
        self.last_config_update = None
    
    # ===================================
    # 配置管理部分
    # ===================================
    
    def load_config(self):
        """从数据库加载配置"""
        try:
            # 加载SMTP配置
            smtp_query = "SELECT * FROM smtp_config WHERE is_active = true ORDER BY created_at DESC LIMIT 1"
            smtp_result = db.execute_query(smtp_query)
            if smtp_result:
                self.smtp_config = smtp_result[0]
            else:
                logger.warning("未找到激活的SMTP配置")
            
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
    
    def get_check_interval(self):
        """获取检查间隔"""
        try:
            return int(self.system_config.get('check_interval', '5'))
        except ValueError:
            return 5
    
    def set_monitor_enabled(self, enabled: bool):
        """设置监控启用状态"""
        query = "UPDATE system_config SET config_value = %s, updated_at = %s WHERE config_key = 'monitor_enabled'"
        result = db.execute_query(query, (str(enabled).lower(), datetime.now()))
        return result is not None
    
    def set_check_interval(self, minutes: int):
        """设置检查间隔"""
        if minutes < 1 or minutes > 60:
            return False
        
        query = "UPDATE system_config SET config_value = %s, updated_at = %s WHERE config_key = 'check_interval'"
        result = db.execute_query(query, (str(minutes), datetime.now()))
        return result is not None
    
    # ===================================
    # 进程管理部分
    # ===================================
    
    def start_process(self) -> Dict[str, Any]:
        """启动监控进程"""
        # 先检查是否已有monitor.py在运行
        existing_pids = self._get_all_monitor_pids()
        if existing_pids:
            return {
                "success": False,
                "message": f"监控进程已在运行中, PID: {existing_pids}",
                "pids": existing_pids,
                "status": "already_running"
            }
        
        try:
            # 启动新的监控进程
            process = subprocess.Popen(
                ["python", self.monitor_script],
                stdout=open(self.log_file, 'a'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # 保存PID到文件
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            logger.info(f"监控进程启动成功, PID: {process.pid}")
            
            return {
                "success": True,
                "message": "监控进程启动成功",
                "pid": process.pid,
                "status": "started",
                "start_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"启动监控进程失败: {e}")
            return {
                "success": False,
                "message": f"启动失败: {str(e)}",
                "status": "start_failed"
            }

    def stop_process(self) -> Dict[str, Any]:
        """停止监控进程"""
        # 获取所有monitor.py进程
        all_pids = self._get_all_monitor_pids()
        
        if not all_pids:
            return {
                "success": False,
                "message": "监控进程未运行",
                "status": "not_running"
            }
        
        stopped_pids = []
        failed_pids = []
        
        try:
            # 方法1: 使用pkill命令（最直接）
            try:
                result = subprocess.run(['pkill', '-f', 'monitor.py'], 
                                    capture_output=True, timeout=5)
                if result.returncode == 0:
                    logger.info("使用 pkill 成功停止 monitor.py 进程")
                time.sleep(2)  # 等待进程完全停止
            except Exception as e:
                logger.warning(f"pkill 执行失败: {e}")
            
            # 方法2: 逐个停止剩余进程
            remaining_pids = self._get_all_monitor_pids()
            for pid in remaining_pids:
                try:
                    # 优雅停止
                    os.kill(pid, signal.SIGTERM)
                    
                    # 等待进程结束
                    for _ in range(5):
                        if not psutil.pid_exists(pid):
                            stopped_pids.append(pid)
                            break
                        time.sleep(1)
                    else:
                        # 强制停止
                        if psutil.pid_exists(pid):
                            os.kill(pid, signal.SIGKILL)
                            stopped_pids.append(pid)
                            logger.warning(f"强制终止进程 PID: {pid}")
                    
                except ProcessLookupError:
                    stopped_pids.append(pid)  # 进程已不存在
                except Exception as e:
                    logger.error(f"停止进程 {pid} 失败: {e}")
                    failed_pids.append(pid)
            
            # 清理PID文件
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            # 验证是否全部停止
            final_check = self._get_all_monitor_pids()
            
            if not final_check:
                logger.info(f"监控进程停止成功, 已停止PID: {stopped_pids}")
                return {
                    "success": True,
                    "message": "监控进程停止成功",
                    "stopped_pids": stopped_pids,
                    "status": "stopped",
                    "stop_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": f"部分进程停止失败, 剩余PID: {final_check}",
                    "stopped_pids": stopped_pids,
                    "failed_pids": final_check,
                    "status": "partial_stopped"
                }
                
        except Exception as e:
            logger.error(f"停止监控进程失败: {e}")
            return {
                "success": False,
                "message": f"停止失败: {str(e)}",
                "stopped_pids": stopped_pids,
                "failed_pids": failed_pids,
                "status": "stop_failed"
            }

    def restart_process(self) -> Dict[str, Any]:
        """重启监控进程"""
        logger.info("开始重启监控进程...")
        
        # 先停止所有进程
        stop_result = self.stop_process()
        
        # 等待确保进程完全停止
        time.sleep(3)
        
        # 再次检查是否还有残留进程
        remaining_pids = self._get_all_monitor_pids()
        if remaining_pids:
            logger.warning(f"发现残留进程: {remaining_pids}，尝试强制清理")
            for pid in remaining_pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                except:
                    pass
            time.sleep(2)
        
        # 启动新进程
        start_result = self.start_process()
        
        success = stop_result.get("success", False) and start_result.get("success", False)
        
        return {
            "success": success,
            "message": f"重启{'成功' if success else '失败'}: 停止-{'成功' if stop_result.get('success') else '失败'}, 启动-{'成功' if start_result.get('success') else '失败'}",
            "stop_result": stop_result,
            "start_result": start_result,
            "status": "restarted" if success else "restart_failed"
        }

    def _get_all_monitor_pids(self) -> list:
        """获取所有monitor.py进程的PID"""
        pids = []
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('monitor.py' in cmd for cmd in cmdline):
                        pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"获取进程列表失败: {e}")
        
        return pids

    def is_process_running(self) -> bool:
        """检查监控进程是否正在运行"""
        return len(self._get_all_monitor_pids()) > 0

    def get_process_status(self) -> Dict[str, Any]:
        """获取监控进程状态"""
        all_pids = self._get_all_monitor_pids()
        
        status_info = {
            "is_running": len(all_pids) > 0,
            "pids": all_pids,
            "status": "running" if all_pids else "stopped",
            "check_time": datetime.now().isoformat()
        }
        
        if all_pids:
            try:
                # 获取第一个进程的详细信息
                main_pid = all_pids[0]
                process = psutil.Process(main_pid)
                status_info.update({
                    "main_pid": main_pid,
                    "start_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                    "cpu_percent": process.cpu_percent(),
                    "memory_info": {
                        "rss": process.memory_info().rss,
                        "vms": process.memory_info().vms
                    },
                    "num_threads": process.num_threads()
                })
            except psutil.NoSuchProcess:
                status_info.update({
                    "is_running": False,
                    "status": "process_not_found",
                    "message": "进程信息获取失败，可能已停止"
                })
        
        return status_info
    
    def get_logs(self, lines: int = 50) -> Dict[str, Any]:
        """获取监控日志"""
        if not os.path.exists(self.log_file):
            return {
                "success": False,
                "message": "日志文件不存在",
                "logs": []
            }
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                # 获取最后N行
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                return {
                    "success": True,
                    "message": f"获取最近{len(recent_lines)}行日志",
                    "total_lines": len(all_lines),
                    "returned_lines": len(recent_lines),
                    "logs": [line.strip() for line in recent_lines]
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"读取日志失败: {str(e)}",
                "logs": []
            }
    
    # ===================================
    # 统一控制接口
    # ===================================
    
    def start_monitor(self) -> Dict[str, Any]:
        """启动监控（配置+进程）"""
        # 1. 启用监控配置
        if not self.set_monitor_enabled(True):
            return {
                "success": False,
                "message": "设置监控配置失败",
                "status": "config_failed"
            }
        
        # 2. 启动监控进程（如果没有运行）
        if not self.is_process_running():
            process_result = self.start_process()
            if not process_result["success"]:
                return process_result
        
        # 3. 重新加载配置
        self.load_config()
        
        return {
            "success": True,
            "message": "监控启动成功",
            "status": "started",
            "config_enabled": True,
            "process_running": self.is_process_running(),
            "start_time": datetime.now().isoformat()
        }
    
    def stop_monitor(self) -> Dict[str, Any]:
        """停止监控（配置+进程）"""
        # 1. 禁用监控配置
        if not self.set_monitor_enabled(False):
            return {
                "success": False,
                "message": "设置监控配置失败",
                "status": "config_failed"
            }
        
        # 2. 停止监控进程（如果在运行）
        if self.is_process_running():
            process_result = self.stop_process()
            if not process_result["success"]:
                return process_result
        
        return {
            "success": True,
            "message": "监控停止成功", 
            "status": "stopped",
            "config_enabled": False,
            "process_running": False,
            "stop_time": datetime.now().isoformat()
        }
    
    def get_monitor_status(self) -> Dict[str, Any]:
        """获取完整监控状态"""
        # 重新加载配置
        self.load_config()
        
        # 获取进程状态
        process_status = self.get_process_status()
        
        # 获取配置状态
        config_enabled = self.is_monitor_enabled()
        email_enabled = self.is_email_enabled()
        check_interval = self.get_check_interval()
        
        return {
            "config": {
                "monitor_enabled": config_enabled,
                "email_enabled": email_enabled,
                "check_interval": check_interval
            },
            "process": process_status,
            "overall_status": "running" if config_enabled and process_status["is_running"] else "stopped",
            "smtp_configured": self.smtp_config is not None,
            "recipients_count": {
                "audit_results": len(self.recipients.get("audit_results", [])),
                "image_audit_results": len(self.recipients.get("image_audit_results", []))
            }
        }