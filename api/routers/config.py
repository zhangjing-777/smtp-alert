from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from database.connection import db
from datetime import datetime

router = APIRouter(prefix="/config", tags=["配置管理"])

class SMTPConfigCreate(BaseModel):
    name: str
    server: str
    port: int = 587
    username: str
    password: str

class SMTPConfigUpdate(BaseModel):
    name: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class RecipientCreate(BaseModel):
    table_name: str
    email: EmailStr
    name: Optional[str] = None

class RecipientUpdate(BaseModel):
    table_name: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None

class SystemConfigUpdate(BaseModel):
    config_value: str
    description: Optional[str] = None

# ===================================
# SMTP配置管理接口
# ===================================

@router.post("/smtp")
async def create_smtp_config(config: SMTPConfigCreate):
    """创建SMTP配置"""
    query = """
    INSERT INTO smtp_config (name, server, port, username, password)
    VALUES (%s, %s, %s, %s, %s) RETURNING id
    """
    result = db.execute_query(query, (config.name, config.server, config.port, 
                                     config.username, config.password))
    if result:
        return {"message": "SMTP配置创建成功", "id": result}
    raise HTTPException(status_code=500, detail="创建失败")

@router.get("/smtp")
async def get_smtp_configs():
    """获取SMTP配置列表"""
    query = "SELECT id, name, server, port, username, is_active, created_at FROM smtp_config ORDER BY created_at DESC"
    configs = db.execute_query(query)
    return {"data": configs or []}

@router.put("/smtp/{config_id}")
async def update_smtp_config(config_id: int, config: SMTPConfigUpdate):
    """更新SMTP配置"""
    # 构建动态更新SQL
    update_fields = []
    update_values = []
    
    for field, value in config.dict(exclude_unset=True).items():
        update_fields.append(f"{field} = %s")
        update_values.append(value)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="没有提供更新字段")
    
    # 添加更新时间
    update_fields.append("updated_at = %s")
    update_values.append(datetime.now())
    update_values.append(config_id)
    
    # 执行更新
    update_query = f"""
        UPDATE smtp_config SET {', '.join(update_fields)}
        WHERE id = %s
    """
    result = db.execute_query(update_query, update_values)
    
    if result is None or result == 0:
        raise HTTPException(status_code=404, detail="SMTP配置不存在")
    
    # 返回更新后的配置
    select_query = "SELECT id, name, server, port, username, is_active, created_at, updated_at FROM smtp_config WHERE id = %s"
    updated_config = db.execute_query(select_query, (config_id,))
    
    if updated_config:
        return {
            "message": "SMTP配置更新成功",
            "data": updated_config[0]
        }
    else:
        raise HTTPException(status_code=500, detail="获取更新后的配置失败")

@router.delete("/smtp/{config_id}")
async def delete_smtp_config(config_id: int):
    """删除SMTP配置"""
    query = "DELETE FROM smtp_config WHERE id = %s"
    result = db.execute_query(query, (config_id,))
    if result and result > 0:
        return {"message": "SMTP配置删除成功"}
    raise HTTPException(status_code=404, detail="配置不存在")

# ===================================
# 收件人管理接口
# ===================================

@router.post("/recipients")
async def create_recipient(recipient: RecipientCreate):
    """添加收件人"""
    query = """
    INSERT INTO recipients_config (table_name, email, name)
    VALUES (%s, %s, %s) RETURNING id
    """
    result = db.execute_query(query, (recipient.table_name, recipient.email, recipient.name))
    if result:
        return {"message": "收件人添加成功", "id": result}
    raise HTTPException(status_code=500, detail="添加失败")

@router.get("/recipients")
async def get_recipients(table_name: Optional[str] = None):
    """获取收件人列表"""
    if table_name:
        query = "SELECT * FROM recipients_config WHERE table_name = %s ORDER BY created_at DESC"
        recipients = db.execute_query(query, (table_name,))
    else:
        query = "SELECT * FROM recipients_config ORDER BY created_at DESC"
        recipients = db.execute_query(query)
    return {"data": recipients or []}

@router.put("/recipients/{recipient_id}")
async def update_recipient(recipient_id: int, recipient: RecipientUpdate):
    """更新收件人信息"""
    # 构建动态更新SQL
    update_fields = []
    update_values = []
    
    for field, value in recipient.dict(exclude_unset=True).items():
        update_fields.append(f"{field} = %s")
        update_values.append(value)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="没有提供更新字段")
    
    # 添加更新时间
    update_fields.append("updated_at = %s")
    update_values.append(datetime.now())
    update_values.append(recipient_id)
    
    # 执行更新
    update_query = f"""
        UPDATE recipients_config SET {', '.join(update_fields)}
        WHERE id = %s
    """
    result = db.execute_query(update_query, update_values)
    
    if result is None or result == 0:
        raise HTTPException(status_code=404, detail="收件人不存在")
    
    # 返回更新后的收件人信息
    select_query = "SELECT * FROM recipients_config WHERE id = %s"
    updated_recipient = db.execute_query(select_query, (recipient_id,))
    
    if updated_recipient:
        return {
            "message": "收件人信息更新成功",
            "data": updated_recipient[0]
        }
    else:
        raise HTTPException(status_code=500, detail="获取更新后的收件人信息失败")

@router.delete("/recipients/{recipient_id}")
async def delete_recipient(recipient_id: int):
    """删除收件人"""
    query = "DELETE FROM recipients_config WHERE id = %s"
    result = db.execute_query(query, (recipient_id,))
    if result and result > 0:
        return {"message": "收件人删除成功"}
    raise HTTPException(status_code=404, detail="收件人不存在")

# ===================================
# 系统配置管理接口
# ===================================

# class SystemConfigCreate(BaseModel):
#     config_key: str
#     config_value: str
#     description: Optional[str] = None

# @router.post("/system")
# async def create_system_config(config: SystemConfigCreate):
#     """创建系统配置"""
#     query = """
#     INSERT INTO system_config (config_key, config_value, description)
#     VALUES (%s, %s, %s) RETURNING id
#     """
#     result = db.execute_query(query, (config.config_key, config.config_value, config.description))
#     if result:
#         return {"message": "系统配置创建成功", "id": result}
#     raise HTTPException(status_code=500, detail="创建失败，可能配置键已存在")

# @router.get("/system")
# async def get_system_configs():
#     """获取系统配置"""
#     query = "SELECT * FROM system_config ORDER BY config_key"
#     configs = db.execute_query(query)
#     return {"data": configs or []}

# @router.get("/system/{config_key}")
# async def get_system_config(config_key: str):
#     """获取单个系统配置"""
#     query = "SELECT * FROM system_config WHERE config_key = %s"
#     config = db.execute_query(query, (config_key,))
#     if config:
#         return {"data": config[0]}
#     raise HTTPException(status_code=404, detail="配置项不存在")

# @router.put("/system/{config_key}")
# async def update_system_config(config_key: str, config: SystemConfigUpdate):
#     """更新系统配置"""
#     # 构建更新SQL
#     update_fields = ["config_value = %s", "updated_at = %s"]
#     update_values = [config.config_value, datetime.now()]
    
#     # 如果提供了描述，也更新描述
#     if config.description is not None:
#         update_fields.append("description = %s")
#         update_values.append(config.description)
    
#     update_values.append(config_key)
    
#     # 执行更新
#     update_query = f"""
#         UPDATE system_config SET {', '.join(update_fields)}
#         WHERE config_key = %s
#     """
#     result = db.execute_query(update_query, update_values)
    
#     if result is None or result == 0:
#         raise HTTPException(status_code=404, detail="配置项不存在")
    
#     # 返回更新后的配置
#     select_query = "SELECT * FROM system_config WHERE config_key = %s"
#     updated_config = db.execute_query(select_query, (config_key,))
    
#     if updated_config:
#         return {
#             "message": "系统配置更新成功", 
#             "data": updated_config[0]
#         }
#     else:
#         raise HTTPException(status_code=500, detail="获取更新后的配置失败")

# @router.delete("/system/{config_key}")
# async def delete_system_config(config_key: str):
#     """删除系统配置"""
#     # 检查是否是核心配置，防止误删
#     core_configs = ['monitor_enabled', 'email_enabled', 'check_interval']
#     if config_key in core_configs:
#         raise HTTPException(status_code=400, detail=f"核心配置项 '{config_key}' 不允许删除")
    
#     query = "DELETE FROM system_config WHERE config_key = %s"
#     result = db.execute_query(query, (config_key,))
#     if result and result > 0:
#         return {"message": "系统配置删除成功"}
#     raise HTTPException(status_code=404, detail="配置项不存在")