# プロジェクト概要

**プロジェクト名**: 競馬シミュレーションアプリ (simulate-keiba)

**説明**: 競馬の結果を予測し、レースを2Dビジュアルでシミュレーションするアプリ
- 実際のレースデータをnetkeiba.comから収集
- 機械学習で着順を予測
- PixiJSで2Dレースアニメーションを表示
- 予測 vs 実際の結果を比較・分析

---

## 目的

このプロジェクトの主な目的:

- [ ] 競馬の結果を予測するアプリを構築する
- [ ] 視覚的にレースの様子を確認できるシミュレーション（2D）を構築する
- [ ] 実際のレース結果から予測の精度を上げられるようにする

---

## 技術スタック

### フロントエンド
- **言語**: TypeScript 5.9+
- **フレームワーク**: React 19 + Vite 7
- **2Dレンダリング**: PixiJS 8
- **ルーティング**: React Router v7
- **テスト**: Vitest + Testing Library
- **リンター/フォーマッター**: ESLint (Flat Config) + Prettier

### バックエンド
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI
- **ORM**: SQLAlchemy 2
- **スクレイピング**: BeautifulSoup4 + httpx
- **機械学習**: scikit-learn + pandas
- **テスト**: pytest + pytest-asyncio
- **リンター**: ruff + mypy

### データベース
- **SQLite** (ローカル・無料・セットアップ不要)

---

## アーキテクチャ方針

### 全体構造
- **フロントエンド**: Vite + React SPA (2Dシミュレーション表示)
- **バックエンド**: FastAPI REST API (データ収集・予測・結果分析)
- **通信**: フロントエンド → `/api/*` → バックエンド (Vite proxy)

### 設計原則
- **関心の分離**: フロントエンド(表示) / バックエンド(ロジック) を明確に分離
- **型安全性**: TypeScript strictモード + Python mypy strict
- **テストファースト**: テストケースを先に書く

---

## ディレクトリ構造

```
simulate-keiba/
├── frontend/                  # React + Vite + PixiJS
│   ├── src/
│   │   ├── api/               # バックエンドAPI呼び出し
│   │   ├── components/        # UIコンポーネント（将来作成）
│   │   ├── simulation/        # レースシミュレーション（PixiJS）
│   │   ├── types/             # 型定義
│   │   └── test/              # テストセットアップ
│   ├── eslint.config.js
│   ├── tsconfig.app.json
│   ├── vite.config.ts
│   └── package.json
│
├── backend/                   # Python FastAPI
│   ├── app/
│   │   ├── api/               # APIエンドポイント
│   │   ├── scraper/           # netkeiba スクレイパー
│   │   ├── predictor/         # 予測エンジン（ML）
│   │   ├── models/            # データモデル（SQLAlchemy）
│   │   └── core/              # 設定・共通処理
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.txt
│
├── data/                      # SQLiteデータベース
├── docs/                      # ドキュメント
├── .editorconfig
├── .gitignore
├── GEMINI.md                  # ← このファイル
├── instructions.md            # タスク定義テンプレート
├── styleguide.md              # コーディング規約
└── README.md
```

---

## 開発ルール

### フロントエンド (TypeScript)
- **TypeScript strict**: すべてのstrictオプション有効化
- **命名規則**:
  - ファイル: `kebab-case.ts` / `PascalCase.tsx` (コンポーネント)
  - クラス/コンポーネント: `PascalCase`
  - 関数/変数: `camelCase`
  - 定数: `UPPER_SNAKE_CASE`
- **パスエイリアス**: `@/` → `src/`
- **テスト**: `__tests__/` ディレクトリに配置

### バックエンド (Python)
- **命名規則**:
  - ファイル: `snake_case.py`
  - クラス: `PascalCase`
  - 関数/変数: `snake_case`
  - 定数: `UPPER_SNAKE_CASE`
- **型ヒント**: すべての関数に型ヒント必須
- **テスト**: `tests/` ディレクトリに配置

### テスト要件
- **カバレッジ**: 80%以上（ユニット + 統合）
- **テストファーストアプローチ**: 実装前にテストケース作成
- **モック**: 外部依存は必ずモック化

---

## 禁止事項

❌ **絶対に使用・実施してはいけないこと**:

### TypeScript
- `any`型の使用（`unknown`を使用する）
- `console.log`の本番コードへの残置

### Python
- 型ヒントなしの関数定義

### 共通
- 環境変数のハードコード
- パスワード・APIキーのコミット
- 未テストコードのマージ
- セキュリティリスクのある外部パッケージ使用

---

## コミット規約

### Conventional Commits準拠

```
type(scope): subject
```

**Type:**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードフォーマット
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・ツール設定

**Scope例**: `frontend`, `backend`, `scraper`, `predictor`, `simulation`

---

## 開発ロードマップ

| Phase | 内容 | 状態 |
|-------|------|------|
| **Phase 0** | プロジェクトセットアップ | ✅ 完了 |
| Phase 1 | データ収集基盤（スクレイパー + DB） | ✅ 完了 |
| Phase 2 | 予測エンジン（特徴量設計 + モデル学習） | ✅ 完了 |
| Phase 3 | レースシミュレーション（PixiJS 2Dアニメーション） | ✅ 完了 |
| Phase 4 | 統合 + UI仕上げ | ✅ 完了 |
| **Phase C** | シミュレーション品質向上（実データ反映・演出強化） | ✅ 完了 |
| **Phase D** | 予測エンジン（着順予測 MVP） | ✅ 完了 |
| **Phase E** | 予測エンジン強化（Ranking Learning + Ensemble） | ✅ 完了 |
| **Phase 5** | ブラッシュアップ（品質向上・UI刷新） | 🔄 進行中 |
| **Phase F** | 高度な特徴量（血統分析・タイム指数） | ⏳ 次回 |
| **Phase G** | データ拡充と検証強化（2024-25データ収集・時系列検証） | ✅ 完了 |

---

## MCP サーバーの活用

効率的な開発のために、以下の MCP サーバーが利用可能です。

- **github**: GitHub リポジトリの操作（ブランチ作成、PR作成、Issue管理など）。
  - **重要**: Git 操作や GitHub 連携が必要な場合は、`run_command` よりも GitHub MCP サーバーのツールを優先的に使用すること。
- **playwright**: ブラウザ自動化と検証。UIの変更確認やインテグレーションテストに使用。
- **filesystem**: ファイルの閲覧、リスト表示、検索。Codebase の理解に不可欠。
- **serena**: 高度なコード分析、リファクタリング支援。シンボルの検索や参照の追跡に使用。

---

## AI開発時の注意

### Antigravityエージェント向け指示

1. **実装前に必ず計画提示**: Implementation Planを作成し承認を待つ
2. **段階的実装**: 大きなタスクは複数のサブタスクに分割
3. **既存コードの尊重**: 既存パターンを壊さない
4. **テストファースト**: 実装前にテストケースを作成
5. **ドキュメント更新**: コード変更時は関連ドキュメントも更新

### コードレビュー基準

- [ ] すべてのテストがパスしている
- [ ] 型エラーがゼロ（TypeScript + mypy）
- [ ] ESLint / ruff 適用済み
- [ ] セキュリティリスクなし
- [ ] ドキュメント更新済み
