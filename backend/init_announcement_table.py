#!/usr/bin/env python3
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='neepu_user',
    password='123456',
    database='neepu'
)

cursor = conn.cursor()

try:
    # 检查 announcement 表是否存在
    cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'neepu' AND TABLE_NAME = 'announcement'
    """)
    
    if not cursor.fetchone():
        print("创建 announcement 表...")
        cursor.execute("""
            CREATE TABLE announcement (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(256) NOT NULL,
                content LONGTEXT NOT NULL,
                creator_id INT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES user(id) ON DELETE SET NULL
            )
        """)
        conn.commit()
        print("✓ announcement 表创建成功")
    else:
        print("✓ announcement 表已存在")

finally:
    cursor.close()
    conn.close()
