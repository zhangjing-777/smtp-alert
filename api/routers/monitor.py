from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from services.unified_monitor_service import UnifiedMonitorService

router = APIRouter(prefix="/monitor", tags=["监控控制"])

# 创建统一监控服务实例
monitor_service = UnifiedMonitorService()

class MonitorResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

@router.post("/start")
async def start_monitor():
    """启动监控（配置+进程）"""
    result = monitor_service.start_monitor()
    
    if result["success"]:
        return MonitorResponse(
            success=True,
            message=result["message"],
            data=result
        )
    else:
        raise HTTPException(
            status_code=400 if result.get("status") == "already_running" else 500,
            detail=result["message"]
        )

@router.post("/stop")
async def stop_monitor():
    """停止监控（配置+进程）"""
    result = monitor_service.stop_monitor()
    
    if result["success"]:
        return MonitorResponse(
            success=True,
            message=result["message"],
            data=result
        )
    else:
        raise HTTPException(
            status_code=400 if result.get("status") == "not_running" else 500,
            detail=result["message"]
        )

@router.post("/restart")
async def restart_monitor():
    """重启监控（配置+进程）"""
    result = monitor_service.restart_process()
    
    if result["success"]:
        return MonitorResponse(
            success=True,
            message=result["message"],
            data=result
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=result["message"]
        )

@router.get("/status")
async def get_monitor_status():
    """获取完整监控状态"""
    status = monitor_service.get_monitor_status()
    return MonitorResponse(
        success=True,
        message="获取状态成功",
        data=status
    )

@router.put("/interval/{minutes}")
async def update_check_interval(minutes: int):
    """更新检查间隔"""
    if minutes < 1 or minutes > 60:
        raise HTTPException(status_code=400, detail="检查间隔必须在1-60分钟之间")
    
    if monitor_service.set_check_interval(minutes):
        return MonitorResponse(
            success=True,
            message=f"检查间隔已更新为{minutes}分钟",
            data={"check_interval": minutes}
        )
    else:
        raise HTTPException(status_code=500, detail="更新检查间隔失败")

@router.get("/logs")
async def get_monitor_logs(lines: int = Query(50, description="获取的日志行数", ge=1, le=1000)):
    """获取监控服务日志"""
    result = monitor_service.get_logs(lines)
    
    if result["success"]:
        return MonitorResponse(
            success=True,
            message=result["message"],
            data=result
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

@router.get("/health")
async def monitor_health_check():
    """监控服务健康检查"""
    status = monitor_service.get_monitor_status()
    
    # 判断服务是否健康
    is_healthy = (status["config"]["monitor_enabled"] and 
                  status["process"]["is_running"])
    
    return {
        "healthy": is_healthy,
        "status": status["overall_status"],
        "message": "监控服务运行正常" if is_healthy else "监控服务未正常运行",
        "timestamp": status["process"]["check_time"]
    }

## 兼容旧接口（可选）
#@router.post("/enable")
#async def enable_monitor():
#    """启用监控功能（仅配置，不启动进程）"""
#    if monitor_service.set_monitor_enabled(True):
#        return {"message": "监控功能已启用"}
#    else:
#        raise HTTPException(status_code=500, detail="启用监控功能失败")

#@router.post("/disable") 
#async def disable_monitor():
#    """禁用监控功能（仅配置，不停止进程）"""
#    if monitor_service.set_monitor_enabled(False):
#        return {"message": "监控功能已禁用"}
#    else:
#        raise HTTPException(status_code=500, detail="禁用监控功能失败")
