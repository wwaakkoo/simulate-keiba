"""
FastAPI アプリケーションのエントリーポイント
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="競馬シミュレーションAPI",
    description="競馬のレースデータ収集・予測・シミュレーションを行うAPI",
    version="0.1.0",
)

# CORS設定（開発時はフロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェックエンドポイント"""
    return {"status": "ok", "version": "0.1.0"}
