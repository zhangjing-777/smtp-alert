/*
===========================================
审计告警系统数据库表结构定义
===========================================
本文件包含审计告警系统所需的所有数据库表结构，
包括SMTP配置、收件人管理、系统配置和邮件发送日志
*/

-- ===================================
-- 1. SMTP邮件服务器配置表
-- ===================================
-- 用途：存储邮件服务器的连接配置信息，支持多个SMTP配置
-- 说明：系统会自动选择最新的激活配置发送邮件
CREATE TABLE IF NOT EXISTS smtp_config (
    id SERIAL PRIMARY KEY,                           -- 自增主键
    name VARCHAR(100) NOT NULL UNIQUE,               -- 配置名称，用于标识不同的SMTP配置（如"公司邮箱"、"备用邮箱"）
    server VARCHAR(255) NOT NULL,                    -- SMTP服务器地址（如smtp.163.com, smtp.qq.com）
    port INTEGER NOT NULL DEFAULT 587,              -- SMTP服务器端口，默认587（TLS加密端口）
    username VARCHAR(255) NOT NULL,                 -- SMTP登录用户名，通常是发送邮件的邮箱地址
    password VARCHAR(255) NOT NULL,                 -- SMTP登录密码或授权码
    is_active BOOLEAN DEFAULT TRUE,                 -- 是否启用此配置，true=启用，false=禁用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 创建时间，记录配置添加时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 更新时间，记录最后修改时间
);

-- ===================================
-- 2. 收件人配置表
-- ===================================
-- 用途：为不同的审计表配置对应的邮件收件人
-- 说明：audit_results表和image_audit_results表可以配置不同的收件人群组
CREATE TABLE IF NOT EXISTS recipients_config (
    id SERIAL PRIMARY KEY,                           -- 自增主键
    table_name VARCHAR(50) NOT NULL,                 -- 监控的表名（audit_results 或 image_audit_results）
    email VARCHAR(255) NOT NULL,                     -- 收件人邮箱地址
    name VARCHAR(100),                               -- 收件人姓名或备注（可选，便于识别）
    is_active BOOLEAN DEFAULT TRUE,                  -- 是否启用，true=接收邮件，false=不接收邮件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间，记录收件人添加时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 更新时间，记录最后修改时间
);

-- ===================================
-- 3. 系统配置表
-- ===================================
-- 用途：存储系统级别的配置参数，如监控开关、检查间隔等
-- 说明：采用键值对形式存储，便于动态配置系统行为
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,                           -- 自增主键
    config_key VARCHAR(100) NOT NULL UNIQUE,         -- 配置项键名（如monitor_enabled、check_interval）
    config_value VARCHAR(500) NOT NULL,              -- 配置项值（如true、false、5）
    description TEXT,                                -- 配置项描述，说明此配置的作用
    is_active BOOLEAN DEFAULT TRUE,                  -- 配置是否生效，预留字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 更新时间，配置修改时自动更新
);

-- ===================================
-- 4. 邮件发送记录表
-- ===================================
-- 用途：记录已发送的邮件，防止对同一条审计记录重复发送邮件
-- 说明：通过table_name+record_id+verdict的组合判断是否已发送过邮件
CREATE TABLE IF NOT EXISTS email_sent_log (
    id SERIAL PRIMARY KEY,                           -- 自增主键
    table_name VARCHAR(50),                          -- 触发邮件的源表名（audit_results 或 image_audit_results）
    record_id INTEGER,                               -- 触发邮件的源记录ID
    verdict VARCHAR(20),                             -- 触发邮件的审计结果（不合格或不确定）
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     -- 邮件发送时间
    recipients TEXT                                  -- 邮件收件人列表，用逗号分隔，便于追踪
);

-- ===================================
-- 插入系统默认配置
-- ===================================
-- 说明：这些是系统运行必需的基础配置
DO $$
BEGIN
    -- 插入 check_interval 配置
    IF NOT EXISTS (SELECT 1 FROM system_config WHERE config_key = 'check_interval') THEN
        INSERT INTO system_config (config_key, config_value, description) 
        VALUES ('check_interval', '5', '监控检查间隔时间（分钟），建议1-30分钟');
    END IF;
    
    -- 插入 monitor_enabled 配置
    IF NOT EXISTS (SELECT 1 FROM system_config WHERE config_key = 'monitor_enabled') THEN
        INSERT INTO system_config (config_key, config_value, description) 
        VALUES ('monitor_enabled', 'true', '监控功能总开关，true=启用监控，false=停止监控');
    END IF;
    
    -- 插入 email_enabled 配置
    IF NOT EXISTS (SELECT 1 FROM system_config WHERE config_key = 'email_enabled') THEN
        INSERT INTO system_config (config_key, config_value, description) 
        VALUES ('email_enabled', 'true', '邮件发送开关，true=发送邮件，false=只记录不发送邮件');
    END IF;
END $$;

-- ===================================
-- 创建索引优化查询性能
-- ===================================
-- 收件人表按表名查询的索引
CREATE INDEX IF NOT EXISTS idx_recipients_table_name ON recipients_config(table_name);

-- 系统配置表按配置键查询的索引
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

-- 邮件日志表按表名和记录ID查询的索引，用于快速判断是否已发送
CREATE INDEX IF NOT EXISTS idx_email_log_table_record ON email_sent_log(table_name, record_id);

-- 邮件日志表按发送时间查询的索引，便于日志清理
CREATE INDEX IF NOT EXISTS idx_email_log_sent_at ON email_sent_log(sent_at);

/*
===========================================
表关系说明：
===========================================

1. smtp_config: 独立表，存储邮件服务器配置
   - 系统自动选择最新的激活配置

2. recipients_config: 独立表，按table_name分组收件人
   - audit_results -> 审计人员邮箱
   - image_audit_results -> 图像管理员邮箱

3. system_config: 系统配置中心
   - 控制整个系统的行为参数

4. email_sent_log: 邮件发送历史
   - 与 audit_results.id 和 image_audit_results.id 关联
   - 防止重复发送邮件

数据流向：
监控程序 -> 查询audit_results/image_audit_results -> 
检查email_sent_log -> 获取recipients_config -> 
使用smtp_config发送邮件 -> 记录到email_sent_log
*/