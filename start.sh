#!/bin/bash
set -e

echo "=== 审计告警系统启动 ==="

# 等待外部数据库连接
echo "等待数据库连接 ${DB_HOST}:${DB_PORT}..."
timeout=60
counter=0
while ! nc -z ${DB_HOST} ${DB_PORT}; do
  sleep 1
  counter=$((counter + 1))
  if [ $counter -gt $timeout ]; then
    echo "❌ 数据库连接超时"
    exit 1
  fi
done
echo "✅ 数据库连接成功"

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