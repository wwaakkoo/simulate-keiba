# プロジェクト履歴 (History)

このファイルは `instructions.md` から移動された完了済みタスクの履歴です。

---

## ✅ 完了済みマイルストーン

### Phase 0: プロジェクトセットアップ
- [x] Frontend: Vite + React + TypeScript セットアップ
- [x] Frontend: ESLint (Flat Config) + Prettier 設定
- [x] Frontend: Vitest + Testing Library 設定
- [x] Frontend: PixiJS + React Router インストール
- [x] Frontend: パスエイリアス (@/) 設定
- [x] Frontend: 型定義 (Race, Horse, Prediction 等)
- [x] Frontend: APIクライアント基盤
- [x] Backend: FastAPI + SQLAlchemy セットアップ
- [x] Backend: ディレクトリ構造 (api, scraper, predictor, models, core)
- [x] Backend: ヘルスチェック API + テスト
- [x] Backend: ruff + mypy 設定
- [x] 共通: .gitignore, .editorconfig, env.example
- [x] ドキュメント: README.md, GEMINI.md 更新

### Phase 1: データ収集基盤
- [x] SQLAlchemy DBモデル定義
- [x] netkeiba.com スクレイパー実装
- [x] データ取得コマンド
- [x] レースデータの収集

### Phase 2: 予測エンジン & API (簡易版)
- [x] 脚質判定ロジック (`logic.py`)
- [x] 馬分析 API (`/api/analysis/horses/{id}`)
- [ ] 予測モデルの構築 (scikit-learn) → ブラッシュアップ Phase D で実施予定

### Phase 3: レースシミュレーション
- [x] PixiJS セットアップ & キャンバス表示
- [x] トラック（コース）の描画
- [x] 馬のスプライト表示
- [x] レース展開ロジック（スタート〜ゴール）
- [x] Scratch/除外馬の対応

### Phase 4: 統合 + UI仕上げ (プロトタイプ)
- [x] フロントエンド全体UI
- [x] レース選択 → シミュレーション の一連フロー
- [ ] 結果分析ダッシュボード → ブラッシュアップ Phase B で実施予定
- [ ] パフォーマンス最適化

### ブラッシュアップ Phase A: 基盤整備 🏗️
- [x] RaceSimulator コンポーネント分割 (576行→約200行+engine/hooks/components)
- [x] 型定義の整理 (types/race.ts 重複解消)
- [x] インラインスタイルのCSS移行 (RaceSimulator.css)
- [x] API呼び出しの改善 (環境変数・N+1解消)

### ブラッシュアップ Phase B: UI/UX刷新 🎨
- [x] デザインシステムの構築 (CSS変数)
- [x] ホームページの刷新 (ダッシュボード化)
- [x] シミュレーション画面の改善 (レース選択UI等)
- [x] 共通コンポーネントライブラリ (Card, Badge等)

### ブラッシュアップ Phase C: シミュレーション品質向上 🎮
- [x] 実レース結果に基づくシミュレーション (RealResultStrategy)
- [x] コース描画の改善 (芝/ダート色分け)
- [x] 馬のビジュアル改善 (シルエット・アニメーション)
- [x] コントロール改善 (速度調整・リセット)

### ブラッシュアップ Phase D: 予測エンジン実装 🤖
- [x] 特徴量エンジニアリング (feature_factory.py)
- [x] 学習モデル構築 (LightGBM + XGBoost)
- [x] 予測APIエンドポイント実装
- [x] 予測結果UIの実装
