"""应用配置：集中管理所有"会随环境变化"的值。

对应文档：docs/08-config-and-env.md
优先级：真实环境变量 > demo/.env 文件 > 下面的默认值
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# demo/ 目录（.env 和 todos.db 都放在这里）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Todo API"
    log_level: str = "INFO"          # 开发时可在 .env 里改成 DEBUG
    db_filename: str = "todos.db"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()    # 全项目 import 这一个实例
