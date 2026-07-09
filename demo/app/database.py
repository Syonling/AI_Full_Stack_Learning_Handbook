"""SQLite 连接管理与建表。

对应文档：docs/05-sqlite-basics.md、docs/07-fastapi-sqlite-crud.md 第 2 节
"""
import sqlite3

from config import BASE_DIR, settings

# 数据库文件放在 app/ 的上一级（demo/todos.db）
# 文件名来自配置（docs/08 章），可用 .env 覆盖
DB_PATH = BASE_DIR / settings.db_filename


def init_db() -> None:
    """建表。应用启动时调用一次，IF NOT EXISTS 保证可重复执行。"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    """FastAPI 依赖函数：每个请求拿到独立连接，请求结束自动关闭。

    yield 之前 = 准备工作；yield 之后 = 收尾工作（见 docs/06 第 6 节 Depends）。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # 让查询结果支持按列名访问
    try:
        yield conn                       # 交给路由函数使用
    finally:
        conn.close()                     # 无论成功还是报错都会关闭
