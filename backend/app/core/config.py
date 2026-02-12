"""
アプリケーション設定

環境変数から設定値を読み込む。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトルート: backend/app/core/config.py -> ... -> simulate-keiba
# 4つ上のディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Settings:
    """アプリケーション設定"""

    # サーバー設定
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # データベース (デフォルト: プロジェクトルート/data/keiba.db)
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/keiba.db"

    # CORS
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    @classmethod
    def from_env(cls) -> "Settings":
        """環境変数から設定を生成"""
        cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        cors_origins = [origin.strip() for origin in cors_raw.split(",")]

        # 環境変数が設定されていればそれを使う、なければ計算したデフォルト値
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            db_url = f"sqlite+aiosqlite:///{BASE_DIR}/data/keiba.db"

        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            database_url=db_url,
            cors_origins=cors_origins,
        )


# グローバル設定インスタンス
settings = Settings.from_env()
