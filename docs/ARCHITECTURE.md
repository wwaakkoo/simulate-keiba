# 🏗️ プロジェクトアーキテクチャ (Map)

このドキュメントは、プロジェクトの主要なファイルとその役割を示した「地図」です。
**AIは実装に取り掛かる前に、まずこのファイルを参照して、修正すべき箇所や参照すべきファイルを特定してください。**

---

## 📂 プロジェクト構成図

```
simulate-keiba/
├── frontend/                  # フロントエンド (React + Vite + PixiJS)
│   ├── src/
│   │   ├── api/               # バックエンドAPI呼び出し (client.ts)
│   │   ├── components/        # Reactコンポーネント (RaceList, AnalysisDashboard等)
│   │   ├── simulation/        # PixiJSによるレースシミュレーションロジック
│   │   │   ├── components/    # シミュレーション用Reactコンポーネント
│   │   │   ├── engine/        # レース展開計算エンジン (positioning, speed)
│   │   │   └── RaceSimulator.tsx # シミュレーションのエントリーポイント
│   │   ├── types/             # TypeScript型定義 (race.ts: ドメインモデル)
│   │   └── App.tsx            # ルーティング定義
│   └── vite.config.ts         # Vite設定 (Proxy設定含む)
│
├── backend/                   # バックエンド (FastAPI + Python)
│   ├── app/
│   │   ├── api/               # APIエンドポイント定義
│   │   │   ├── routes.py      # 主要なルーター定義 (GET /races, POST /predict)
│   │   │   └── schemas.py     # APIレスポンス用Pydanticモデル
│   │   ├── core/              # 設定・共通ユーティリティ (config.py, database.py)
│   │   ├── models/            # SQLAlchemy DBモデル (race.py, horse.py)
│   │   ├── predictor/         # 予測エンジン (Machine Learning)
│   │   │   ├── features.py    # 特徴量エンジニアリング (Focus here for ML tasks)
│   │   │   ├── trainer.py     # モデル学習スクリプト (LightGBM/XGBoost)
│   │   │   └── logic.py       # ルールベースの簡易ロジック (脚質判定等)
│   │   └── scraper/           # データ収集スクリプト
│   │       ├── client.py      # HTTPクライアント (netkeibaへのリクエスト)
│   │       ├── parser.py      # HTML解析 (BeautifulSoup)
│   │       └── service.py     # スクレイピングのオーケストレーション
│   └── main.py                # アプリケーションエントリーポイント
│
├── data/                      # データ永続化 (SQLite)
└── docs/                      # ドキュメント (これ!)
```

---

## 🔑 主要ファイルの役割詳細

### Frontend (`frontend/src/`)

| パス | 役割 | 関連タスク |
|---|---|---|
| `components/RaceList.tsx` | レース一覧表示・検索 | UI改善, フィルタリング |
| `simulation/RaceSimulator.tsx` | シミュレーション画面の親コンポーネント | 表示制御, State管理 |
| `simulation/engine/*.ts` | 物理演算・レース展開ロジック | リアルな動き, 展開調整 |
| `types/race.ts` | **最重要**: レース・馬・予測の型定義 | データ構造変更 |

### Backend (`backend/app/`)

| パス | 役割 | 関連タスク |
|---|---|---|
| `models/*.py` | データベーススキーマ定義 | DBマイグレーション |
| `scraper/parser.py` | HTMLからのデータ抽出ロジック | スクレイピング精度向上 |
| `predictor/features.py` | **ML**: 学習用特徴量の生成ロジック | 予測精度向上, 新指標追加 |
| `predictor/trainer.py` | **ML**: モデルの学習・評価・保存 | モデル更新, ハイパーパラメータ調整 |
| `api/routes.py` | APIエンドポイントの実装 | 新機能API追加 |

---

## 🚫 AI読み込み推奨外のファイル (No-Go Zone)

以下のファイルはサイズが大きく、AIのコンテキストを圧迫するため、**必要な場合を除き読み込まないでください**。

- `frontend/package-lock.json`
- `backend/uv.lock`
- `frontend/dist/*`
- `backend/.venv/*`
- `backend/app/scraper/debug_*.html` (デバッグ用HTMLダンプ)

---

## 📝 開発のヒント

1. **データ構造の変更**: まず `backend/app/models/` と `frontend/src/types/` の両方を更新してください。
2. **APIの追加**: `backend/app/api/schemas.py` で型を定義し、`routes.py` に実装 → `frontend/src/api/client.ts` にメソッド追加の流れがスムーズです。
3. **ML実験**: `backend/app/predictor/` 内で完結させ、`scripts/` に実験用スクリプトを作成することを推奨します。
