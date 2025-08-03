# 审计告警配置管理控制系统

一个基于FastAPI的审计告警系统，用于监控数据库中的审计结果并自动发送邮件通知。系统支持SMTP邮件配置管理、收件人管理、监控进程控制等功能。

## 🚀 功能特性

### 核心功能
- **审计结果监控**: 自动监控 `audit_results` 和 `image_audit_results` 表中的不合格/不确定记录
- **邮件告警**: 支持HTML格式的邮件通知，包含详细的审计信息
- **防重复发送**: 通过邮件发送日志避免对同一记录重复发送邮件
- **实时监控**: 可配置的检查间隔，支持1-60分钟的动态调整

### 配置管理
- **SMTP配置管理**: 支持多个SMTP服务器配置，可动态切换
- **收件人管理**: 按表名分组管理收件人，支持批量操作
- **系统配置**: 监控开关、邮件开关、检查间隔等系统级配置

### 进程控制
- **统一监控服务**: 整合配置控制和进程管理
- **进程状态监控**: 实时查看监控进程的运行状态
- **日志管理**: 支持查看监控服务的运行日志
- **健康检查**: 提供API健康检查接口

## 📁 项目结构

```
smtp-alert/
├── api/                          # API服务层
│   ├── main.py                   # FastAPI主应用
│   └── routers/                  # 路由模块
│       ├── config.py             # 配置管理API
│       └── monitor.py            # 监控控制API
├── config/                       # 配置管理
│   └── settings.py               # 应用配置
├── database/                     # 数据库相关
│   ├── connection.py             # 数据库连接
│   ├── init.sql                  # 数据库初始化脚本
│   └── run.py                    # 数据库初始化工具
├── services/                     # 业务服务层
│   ├── email_service.py          # 邮件服务
│   ├── monitor_service.py        # 监控服务
│   └── unified_monitor_service.py # 统一监控服务
├── monitor.py                    # 监控主程序
├── requirements.txt              # Python依赖
├── Dockerfile                    # Docker镜像构建
├── docker-compose.yml            # Docker编排配置
├── start.sh                      # 启动脚本
└── README.md                     # 项目文档
```

## 🛠️ 技术栈

- **后端框架**: FastAPI
- **数据库**: PostgreSQL
- **邮件服务**: SMTP
- **进程管理**: psutil
- **定时任务**: schedule
- **容器化**: Docker & Docker Compose
- **日志**: Python logging

## 📋 数据库设计

### 核心表结构

#### 1. smtp_config (SMTP配置表)
```sql
- id: 自增主键
- name: 配置名称
- server: SMTP服务器地址
- port: 端口号
- username: 用户名
- password: 密码
- is_active: 是否启用
- created_at/updated_at: 时间戳
```

#### 2. recipients_config (收件人配置表)
```sql
- id: 自增主键
- table_name: 监控的表名
- email: 收件人邮箱
- name: 收件人姓名
- is_active: 是否启用
- created_at/updated_at: 时间戳
```

#### 3. system_config (系统配置表)
```sql
- id: 自增主键
- config_key: 配置键
- config_value: 配置值
- description: 配置描述
- is_active: 是否生效
- created_at/updated_at: 时间戳
```

#### 4. email_sent_log (邮件发送日志表)
```sql
- id: 自增主键
- table_name: 源表名
- record_id: 源记录ID
- verdict: 审计结果
- sent_at: 发送时间
- recipients: 收件人列表
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- Docker & Docker Compose (可选)

### 1. 环境变量配置

创建 `.env` 文件：

```bash
# API配置
API_HOST=0.0.0.0
API_PORT=8000

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=audit_alert
DB_USER=postgres
DB_PASSWORD=your_password
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/audit_alert

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=audit_alert.log
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库初始化

```bash
cd database
python run.py
```

### 4. 启动服务

#### 方式一：直接运行
```bash
# 启动API服务
python -m api.main

# 启动监控服务（新终端）
python monitor.py
```

#### 方式二：Docker部署
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 📚 API文档

### 基础信息
- **API地址**: `http://localhost:8000`
- **文档地址**: `http://localhost:8000/docs`
- **健康检查**: `http://localhost:8000/health`

### 主要接口

#### 配置管理接口 (`/api/config`)

##### SMTP配置管理
```http
POST   /api/config/smtp          # 创建SMTP配置
GET    /api/config/smtp          # 获取SMTP配置列表
PUT    /api/config/smtp/{id}     # 更新SMTP配置
DELETE /api/config/smtp/{id}     # 删除SMTP配置
```

##### 收件人管理
```http
POST   /api/config/recipients          # 添加收件人
GET    /api/config/recipients          # 获取收件人列表
PUT    /api/config/recipients/{id}     # 更新收件人
DELETE /api/config/recipients/{id}     # 删除收件人
```

#### 监控控制接口 (`/api/monitor`)

```http
POST   /api/monitor/start              # 启动监控
POST   /api/monitor/stop               # 停止监控
POST   /api/monitor/restart            # 重启监控
GET    /api/monitor/status             # 获取监控状态
PUT    /api/monitor/interval/{minutes} # 更新检查间隔
GET    /api/monitor/logs               # 获取监控日志
GET    /api/monitor/health             # 监控健康检查
```

### 请求示例

#### 创建SMTP配置
```bash
curl -X POST "http://localhost:8000/api/config/smtp" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "公司邮箱",
    "server": "smtp.163.com",
    "port": 587,
    "username": "your_email@163.com",
    "password": "your_password"
  }'
```

#### 添加收件人
```bash
curl -X POST "http://localhost:8000/api/config/recipients" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "audit_results",
    "email": "admin@company.com",
    "name": "管理员"
  }'
```

#### 启动监控
```bash
curl -X POST "http://localhost:8000/api/monitor/start"
```

## 🔧 配置说明

### 系统配置项

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `monitor_enabled` | `true` | 监控功能总开关 |
| `email_enabled` | `true` | 邮件发送开关 |
| `check_interval` | `5` | 检查间隔（分钟） |

### 监控配置

- **检查间隔**: 1-60分钟，建议5-15分钟
- **监控表**: `audit_results` 和 `image_audit_results`
- **触发条件**: 审计结果为"不合格"或"不确定"
- **防重复**: 通过 `email_sent_log` 表避免重复发送

## 📊 监控状态

### 状态检查
```bash
curl http://localhost:8000/api/monitor/status
```

返回示例：
```json
{
  "config": {
    "monitor_enabled": true,
    "email_enabled": true,
    "check_interval": 5
  },
  "process": {
    "is_running": true,
    "pid": 12345,
    "status": "running",
    "start_time": "2024-01-01T10:00:00"
  },
  "overall_status": "running",
  "smtp_configured": true,
  "recipients_count": {
    "audit_results": 2,
    "image_audit_results": 1
  }
}
```

## 🔍 日志管理

### 查看监控日志
```bash
curl "http://localhost:8000/api/monitor/logs?lines=100"
```

### 日志文件位置
- **API日志**: `audit_alert.log`
- **监控日志**: `monitor.log`
- **Docker日志**: `docker-compose logs -f`

## 🐳 Docker部署

### 构建镜像
```bash
docker build -t smtp-alert .
```

### 使用Docker Compose
```bash
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 环境变量配置
在 `docker-compose.yml` 中配置环境变量，或使用 `.env` 文件。

## 🔒 安全考虑

1. **密码加密**: SMTP密码建议使用环境变量或加密存储
2. **访问控制**: 生产环境建议添加API认证
3. **日志安全**: 敏感信息不应记录在日志中
4. **网络安全**: 建议使用HTTPS和防火墙保护

## 🚨 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证连接参数是否正确
   - 确认网络连通性

2. **邮件发送失败**
   - 检查SMTP配置是否正确
   - 验证邮箱授权码
   - 确认防火墙设置

3. **监控进程异常**
   - 检查PID文件是否存在
   - 查看监控日志
   - 重启监控服务

### 调试命令

```bash
# 检查进程状态
ps aux | grep monitor.py

# 查看端口占用
netstat -tlnp | grep 8000

# 检查数据库连接
python -c "from database.connection import db; print(db.get_connection())"
```

## 📝 开发指南

### 添加新的监控表

1. 在 `monitor_service.py` 中添加新的检查方法
2. 在 `email_service.py` 中添加对应的邮件模板
3. 配置收件人信息
4. 更新数据库初始化脚本

### 扩展API接口

1. 在 `api/routers/` 下创建新的路由文件
2. 在 `api/main.py` 中注册路由
3. 添加相应的数据模型和业务逻辑

