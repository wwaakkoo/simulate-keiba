# 作業指示書 — 競馬シミュレーションアプリ

> **このファイルはAntigravityエージェントへの作業指示を記載するファイルです。**
> 使い方: `@instructions.md @GEMINI.md` でチャットに参照

---

## 📋 現在のタスク

**タスク概要**: Phase 1 実装中 — データ収集基盤

**優先度**: 高

**最終更新**: 2026-02-12

---

## ✅ 完了済みタスク

### Phase 0: プロジェクトセットアップ ✅
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

---

## 🗺️ 次フェーズの概要

### Phase 1: データ収集基盤 🚧
- [x] SQLAlchemy DBモデル定義（Race, Horse, RaceEntry）
- [x] HTMLパーサー（netkeiba.com レース結果ページ）
- [x] HTTPクライアント（レート制限・リトライ付き）
- [x] スクレイパーサービス（パーサー + クライアント + DB保存統合）
- [x] Pydanticスキーマ（API入出力型定義）
- [x] APIエンドポイント（scrape, races, horses）
- [x] モックHTMLによるパーサーテスト
- [x] APIエンドポイントテスト
- [ ] 実データでの動作検証
- [ ] フロントエンドとの結合テスト

### Phase 2: 予測エンジン
- [ ] 特徴量設計（馬・騎手・コース等）
- [ ] モデル学習パイプライン
- [ ] 予測 API エンドポイント
- [ ] モデル評価・精度検証

### Phase 3: レースシミュレーション
- [ ] PixiJS 2Dレースビュー実装
- [ ] 馬のスプライト・アニメーション
- [ ] コース描画（芝/ダート）
- [ ] レース進行ロジック

### Phase 4: 統合 + UI仕上げ
- [ ] フロントエンド全体UI
- [ ] レース選択 → 予測 → シミュレーション の一連フロー
- [ ] 結果分析ダッシュボード
- [ ] パフォーマンス最適化

---

## 🔄 Antigravityでの作業フロー

### 新機能の実装

```
@instructions.md @GEMINI.md

[タスクの詳細]を実装してください。
まず実装計画を提示してください。
```

### バグ修正

```
@instructions.md

次のエラーが発生しています:
[エラーメッセージ]

原因を特定して修正してください。
修正後はテストケースも追加してください。
```

---

## ⚠️ 開発時の注意事項

### 実装前チェックリスト
- [ ] GEMINI.md の禁止事項を確認
- [ ] 実装計画を提示し承認を得る
- [ ] テストケースを先に設計

### コミット前チェックリスト
- [ ] Frontend: `npm run type-check` → エラーなし
- [ ] Frontend: `npm run lint` → エラーなし
- [ ] Frontend: `npm test` → 全パス
- [ ] Backend: `ruff check app/` → エラーなし
- [ ] Backend: `pytest tests/ -v` → 全パス

---

## 📚 参照すべきファイル

**必ず参照:**
- `@GEMINI.md` — プロジェクト全体のルール・技術スタック
- `@styleguide.md` — コーディングスタイルガイド

**コード参照（タスクに応じて）:**
- `@frontend/src/types/race.ts` — ドメイン型定義
- `@frontend/src/api/client.ts` — APIクライアント
- `@backend/app/main.py` — FastAPIエントリーポイント
- `@backend/app/core/config.py` — 設定クラス
