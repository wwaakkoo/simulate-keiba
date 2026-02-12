"""
データベース初期化

テーブルの作成を行う。
アプリケーション起動時に呼ばれる。
"""

from app.core.database import engine
from app.models import Base


async def init_db() -> None:
    """全テーブルを作成する（存在しない場合のみ）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """全テーブルを削除する（テスト用）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
