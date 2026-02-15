# 🏇 競馬シミュレーションアプリ

> 競馬の結果を予測し、2Dビジュアルでレースをシミュレーションするアプリ

[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.13-green)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📖 概要

競馬のレースデータを収集し、機械学習で着順を予測。さらにレースの様子を2Dアニメーションで視覚的に再現するシミュレーションアプリです。

### 主な機能

- 🏇 **レースシミュレーション**: PixiJSによる2Dレースアニメーション
- 🤖 **AI予測エンジン**: 機械学習でレース結果を予測
- 📊 **データ収集**: netkeiba.comからレースデータを自動収集
- 📈 **結果分析**: 予測 vs 実際の結果を比較して精度改善

## 🏃 使い方の流れ (データの取得と予測)

特定のレースを予測・シミュレーションしたい場合は、以下の手順で行います。

### 1. レースIDを確認する
netkeibaのURLから取得したいレースのID（12桁の数字）を探します。  
例: `https://db.netkeiba.com/race/202406050811/` の場合、IDは `202406050811` です。

### 2. レースデータの取得 (Scrape)
ターミナルまたはブラウザのSwagger UIから、データをDBに取り込みます。
```bash
curl -X POST http://localhost:8000/api/scrape/race -H "Content-Type: application/json" -d "{\"race_id\": \"202406050811\"}"
```

### 3. AI予測の実行 (Predict)
データ取得後、以下のAPIを叩くとAIの予測結果（印やスコア）が返ってきます。
```bash
curl -X POST http://localhost:8000/api/races/202406050811/predict
```

### 4. 画面での表示
ブラウザで以下のURLにアクセスすると、予測結果の確認とシミュレーションが可能です。  
`http://localhost:5173/races/任意のレースID`

---

## 🛠️ 技術スタック

| レイヤー | 技術 |
|---------|------|
| **フロントエンド** | React 19 + Vite 7 + TypeScript 5.9 |
| **2Dレンダリング** | PixiJS 8 |
| **バックエンド** | Python 3.13 + FastAPI |
| **データベース** | SQLite (SQLAlchemy 2) |
| **ML** | scikit-learn + pandas |
| **スクレイピング** | BeautifulSoup4 + httpx |
| **テスト** | Vitest (Frontend) / pytest (Backend) |

---

## 🚀 セットアップ

### 前提条件

- Node.js 20+
- Python 3.11+
- npm

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

### バックエンド

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
```

### 開発サーバー

フロントエンド（ http://localhost:5173 ）とバックエンド（ http://localhost:8000 ）を同時に起動してください。
Viteのプロキシ設定により、フロントエンドから `/api/*` へのリクエストは自動的にバックエンドに転送されます。

---

## 📁 プロジェクト構造

```
simulate-keiba/
├── frontend/                  # React + Vite + PixiJS
│   ├── src/
│   │   ├── api/               # バックエンドAPI呼び出し
│   │   ├── components/        # UIコンポーネント
│   │   ├── simulation/        # レースシミュレーション（PixiJS）
│   │   ├── types/             # 型定義
│   │   └── test/              # テストセットアップ
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                   # Python FastAPI
│   ├── app/
│   │   ├── api/               # APIエンドポイント
│   │   ├── scraper/           # netkeiba スクレイパー
│   │   ├── predictor/         # 予測エンジン（ML）
│   │   ├── models/            # データモデル
│   │   └── core/              # 設定・共通処理
│   ├── tests/
│   └── pyproject.toml
│
├── data/                      # SQLiteデータベース
├── docs/                      # ドキュメント
└── GEMINI.md                  # AI開発用設定
```

---

## 🧪 テスト

```bash
# フロントエンド
cd frontend
npm test              # テスト実行
npm run test:watch    # ウォッチモード
npm run test:coverage # カバレッジ付き

# バックエンド
cd backend
.venv\Scripts\python -m pytest tests/ -v     # テスト実行
.venv\Scripts\python -m pytest --cov=app     # カバレッジ付き
```

---

## 📝 開発コマンド一覧

### フロントエンド

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバー起動 |
| `npm run build` | プロダクションビルド |
| `npm run type-check` | TypeScript型チェック |
| `npm run lint` | ESLintチェック |
| `npm run lint:fix` | ESLint自動修正 |
| `npm run format` | Prettier整形 |
| `npm test` | テスト実行 |

### バックエンド

| コマンド | 説明 |
|---------|------|
| `uvicorn app.main:app --reload` | 開発サーバー起動 |
| `python -m pytest tests/ -v` | テスト実行 |
| `python -m ruff check app/` | リントチェック |
| `python -m mypy app/` | 型チェック |

---

## 🗺️ 開発ロードマップ

| Phase | 内容 | 状態 |
|-------|------|------|
| Phase 0 | プロジェクトセットアップ | ✅ 完了 |
| Phase 1 | データ収集基盤（スクレイパー + DB） | ✅ 完了 |
| Phase 2 | 予測エンジン（特徴量設計 + モデル学習） | ✅ 完了 |
| Phase 3 | レースシミュレーション（PixiJS 2Dアニメーション） | ✅ 完了 |
| Phase 4 | 統合 + UI仕上げ | ⬜ 未着手 |

---

## 📄 ライセンス

[MIT License](LICENSE)
