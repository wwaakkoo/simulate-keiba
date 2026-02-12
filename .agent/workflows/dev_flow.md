---
description: 開発フローとコーディング規約
---

# 開発フロー (simulate-keiba)

## 1. 開発の基本原則
- **型安全性の徹底**: TypeScript は strict モード、Python は型ヒントを必須とします。
- **テストファースト**: 新機能やバグ修正の際は、まずテストコードを作成または更新してください。
- **ドキュメント更新**: コードの変更に合わせて `GEMINI.md` や `walkthrough.md` を更新してください。

## 2. フロントエンド開発 (Vite + React + PixiJS)
- **コマンド**: `npm run dev` で開発サーバを起動
- **Lint**: `npm run lint`
- **テスト**: `npm run test`

## 3. バックエンド開発 (FastAPI)
- **コマンド**: `uvicorn app.main:app --reload`
- **Lint**: `ruff check .`
- **テスト**: `pytest`

## 4. Git 規約
- Conventional Commits に準拠してください。
  - `feat`: 新機能
  - `fix`: バグ修正
  - `docs`: 文書
  - `style`: フォーマット
  - `refactor`: リファクタリング
  - `test`: テスト
  - `chore`: その他雑事
