"""
FastAPI アプリケーションのエントリーポイント
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.init_db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """アプリケーションのライフサイクル管理"""
    # 起動時: DBテーブル初期化
    await init_db()
    yield
    # 終了時: 必要ならクリーンアップ処理


app = FastAPI(
    title="競馬シミュレーションAPI",
    description="競馬のレースデータ収集・予測・シミュレーションを行うAPI",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS設定（開発時はフロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(api_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェックエンドポイント"""
    return {"status": "ok", "version": "0.1.0"}
