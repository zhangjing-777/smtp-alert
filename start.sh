#!/bin/bash
set -e

echo "=== 审计告警系统启动 ==="

# 等待外部数据库连接（使用Python替代nc命令）
echo "等待数据库连接 ${DB_HOST}:${DB_PORT}..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    # 使用Python检测端口连接
    if python3 -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('${DB_HOST}', ${DB_PORT}))
    sock.close()
    if result == 0:
        sys.exit(0)
    else:
        sys.exit(1)
except:
    sys.exit(1)
" 2>/dev/null; then
        echo "✅ 数据库连接成功"
        break
    fi
    
    sleep 1
    counter=$((counter + 1))
    if [ $counter -eq $timeout ]; then
        echo "❌ 数据库连接超时"
        exit 1
    fi
done

# 测试数据库连接
echo "测试数据库连接..."
python3 -c "
import psycopg
try:
    conn = psycopg.connect(
        host='${DB_HOST}',
        port=${DB_PORT},
        dbname='${DB_NAME}',
        user='${DB_USER}',
        password='${DB_PASSWORD}'
    )
    print('✅ 数据库连接测试成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接测试失败: {e}')
    exit(1)
"

# 在后台启动 monitor.py
echo "启动监控服务..."
python3 monitor.py &
MONITOR_PID=$!
echo "✅ 监控服务已启动 (PID: $MONITOR_PID)"

# 启动 FastAPI 服务
echo "启动 API 服务..."
exec python3 -m api.main