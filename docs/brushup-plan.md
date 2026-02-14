# 🏇 ブラッシュアップ計画 — プロトタイプ → 製品品質

> **作成日**: 2026-02-13
> **現状**: 全Phase (0〜4) のプロトタイプ実装完了
> **目標**: 実用的で美しく、信頼性の高いシミュレーションアプリへ

---

## 📋 概要

現状のプロトタイプには以下の課題があります：

| 領域 | 現状 | 課題の深刻度 |
|------|------|-------------|
| シミュレーション品質 | 脚質ベースの簡易ロジック | 🔴 高 |
| UI/UX | インラインスタイル中心、基本的なレイアウト | 🔴 高 |
| コード品質 | 576行の巨大コンポーネント、重複型定義 | 🟡 中 |
| 予測エンジン | 脚質判定のみ（MLモデルなし） | 🟡 中 |
| テスト | フロントエンドのテストが薄い | 🟡 中 |
| パフォーマンス | 馬分析APIをN+1で呼び出し | 🟡 中 |
| ドキュメント・メンテ | instructions.md が古い、DB容量小 | 🟢 低 |

---

## 🗺️ ブラッシュアップロードマップ

### 推奨実施順序

```
Phase A (基盤整備)       → すべての土台
Phase B (UI/UX刷新)      → ユーザー体験の劇的改善
Phase C (シミュ品質向上)  → コア機能の本質的改善
Phase D (予測エンジン)    → 差別化機能
Phase E (テスト・品質)    → 安定性確保
Phase F (運用・デプロイ)  → 本番運用対応
```

---

## Phase A: 基盤整備（コード品質・アーキテクチャ） 🔧

**優先度: 最高** | **見積もり: 2〜3日**

他のすべての改善の土台となる作業です。

### A-1. RaceSimulator コンポーネントの分割

**現状の問題**: `RaceSimulator.tsx` が576行の巨大コンポーネントで、描画ロジック・状態管理・UI がすべて混在

**改善案**:
```
simulation/
├── RaceSimulator.tsx          # メインコンテナ（状態管理 + レイアウト）
├── components/
│   ├── RaceSelector.tsx       # レース選択UI
│   ├── SimulationCanvas.tsx   # PixiJSキャンバス管理
│   ├── SimControls.tsx        # 速度調整・開始/リセットボタン
│   ├── RankingPanel.tsx       # シミュレーション結果順位
│   └── EntryTable.tsx         # 出走馬詳細テーブル
├── hooks/
│   ├── usePixiApp.ts          # PixiJSアプリケーション初期化
│   ├── useRaceData.ts         # レースデータフェッチ
│   └── useSimulation.ts       # シミュレーションロジック
├── engine/
│   ├── TrackRenderer.ts       # コース描画ロジック
│   ├── SimulationEngine.ts    # 走行シミュレーション計算
│   └── PositionCalculator.ts  # コース上の座標計算
├── models/
│   └── HorseSprite.ts         # 馬のスプライト
├── config.ts
└── index.ts
```

### A-2. 型定義の整理

**現状の問題**: `types/race.ts` と `types/index.ts` で重複する型定義

**改善案**:
- `types/race.ts` をAPIレスポンス型のみに統合（`types/index.ts` が実使用中）
- `types/race.ts` の `Horse`, `Race`, `Prediction` 等のドメイン型を精査
  - 使われていないなら削除、使うなら `types/domain.ts` に分離
- フロントエンドの型をバックエンドのPydantic schemaから自動生成する仕組みの導入を検討

### A-3. インラインスタイルの排除

**現状の問題**: `RaceSimulator.tsx` 内に約100箇所のインラインスタイル

**改善案**:
- CSS Modulesまたは専用CSSファイルに移行
- デザイントークン（色・フォントサイズ・spacing）をCSS変数化
- コンポーネント分割（A-1）と同時に実施

### A-4. API呼び出しの改善

**現状の問題**: 
- `raceApi.ts` でベースURLが `http://localhost:8000/api` にハードコード
- 馬分析APIをN+1で呼び出し（出走馬ごとに1リクエスト）

**改善案**:
- 環境変数から API ベースURLを取得（`import.meta.env.VITE_API_BASE`）
- バックエンドに一括分析エンドポイント追加: `GET /api/races/{id}/analysis`
- エラーハンドリングの統一（トースト通知など）

---

## Phase B: UI/UX刷新 🎨

**優先度: 高** | **見積もり: 3〜5日**

ユーザーが最初に触れる部分であり、印象を大きく左右します。

### B-1. デザインシステムの構築

**改善案**:
```css
/* design-tokens.css */
:root {
  /* Colors */
  --color-primary: #2563eb;
  --color-primary-dark: #1d4ed8;
  --color-surface: #ffffff;
  --color-background: #0f172a;
  
  /* Typography */
  --font-display: 'Noto Sans JP', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  
  /* ダークモード対応 */
  --shadow-card: 0 4px 16px rgba(0, 0, 0, 0.08);
}
```

### B-2. ホームページの刷新

**現状の問題**: 簡素なステータス表示のみ

**改善案**:
- ダッシュボード形式に変更
  - 本日のレース一覧カード
  - 最近のシミュレーション結果サマリー
  - DB内のデータ統計（総レース数、馬数、期間）
- ダークモード対応のリッチなデザイン
- レスポンシブ対応（モバイルでも閲覧可能に）

### B-3. シミュレーション画面の改善

**現状の問題**: 基本的なレイアウト、情報密度が低い

**改善案**:
- **レース選択**: カレンダービューまたはカード型選択UI
- **シミュレーション画面**: 
  - リアルタイム順位表示（レース中に変動するランキング）
  - 通過タイム表示（1コーナー、2コーナー等）
  - 馬のホバーで詳細情報表示
- **結果画面**: 
  - シミュ結果 vs 実際の結果の比較ビジュアル
  - 的中/不的中のハイライト
  - 着差のビジュアル表現

### B-4. 共通コンポーネントライブラリ

**追加すべきコンポーネント**:
```
components/
├── common/
│   ├── Card.tsx               # カードコンテナ
│   ├── Badge.tsx              # ステータスバッジ（脚質表示等）
│   ├── Loading.tsx            # ローディングスピナー
│   ├── Toast.tsx              # 通知トースト
│   └── Header.tsx             # 共通ヘッダー + ナビゲーション
├── race/
│   ├── RaceCard.tsx           # レース情報カード
│   ├── HorseCard.tsx          # 馬情報カード
│   ├── OddsDisplay.tsx        # オッズ表示
│   └── BracketBadge.tsx       # 枠番バッジ（色付き）
└── charts/
    ├── ComparisonChart.tsx     # 予測 vs 実際の比較チャート
    └── TimelineChart.tsx      # 通過順タイムライン
```

---

## Phase C: シミュレーション品質の向上 🎮

**優先度: 高** | **見積もり: 3〜4日**

コア機能の本質的な改善です。

### C-1. 実際のレース結果に基づくシミュレーション

**現状の問題**: 
- 脚質（逃げ/先行/差し/追込）による速度配分のみ
- `stats.speed` が分析APIから取得されるが暫定的な値
- シミュ結果と実際の結果が大きく乖離する

**改善案**:
- **通過順データの活用**: `passing_order` ("3-3-2-1") を使って各コーナーでの実際の順位変動を再現
- **走破タイムの活用**: `finish_time` からゴールタイミングを正確に設定
- **着差データの活用**: `margin` ("1/2", "クビ") からゴール時の間隔を算出
- **上がり3Fの活用**: `last_3f` でラストスパートの加速度を決定

```typescript
// 改善版: 実データ駆動のシミュレーション
interface SimulationPlan {
  checkpoints: { // 各通過地点での目標順位
    position: number;  // コース上の位置 (0.0 ~ 1.0)
    targetRank: number; // その地点での順位
  }[];
  finishTime: number;   // 走破タイム (秒)
  last3fSpeed: number;  // 上がり3Fの速度
}
```

### C-2. コース描画の改善

**現状の問題**: 単純な楕円トラックのみ

**改善案**:
- 内馬場・外馬場の視覚的区別
- 距離に応じたスタート位置マーカー
- コーナー番号の表示
- 芝/ダートの色分け
- ゴール板のビジュアル強化

### C-3. 馬のビジュアル改善

**現状の問題**: 枠番色の単純な円

**改善案**:
- 馬のシルエット画像（簡易的なベクター）
- 走行アニメーション（足の動き）
- 先頭馬のハイライトエフェクト
- ゴール時の着順表示エフェクト

### C-4. リプレイ・スロー再生機能

- シミュレーション完了後のリプレイ
- ゴール前のスローモーション
- 特定の馬を追跡するカメラ機能

---

## Phase D: 予測エンジンの強化 🤖

**優先度: 中** | **見積もり: 5〜7日**

アプリの差別化ポイントとなる機能ですが、データ量が必要なため段階的に実装。

### D-1. 特徴量設計

```python
# 候補となる特徴量
features = {
    # 馬の基本能力
    "avg_finish_position": "過去の平均着順",
    "win_rate": "勝率",
    "place_rate": "複勝率",
    "avg_speed_rating": "平均スピード指数",

    # コース適性
    "course_type_win_rate": "芝/ダート別勝率",
    "distance_win_rate": "距離帯別勝率",
    "venue_win_rate": "競馬場別勝率",
    "track_condition_win_rate": "馬場状態別勝率",
    
    # 直近の調子
    "recent_3_avg_position": "直近3走の平均着順",
    "days_since_last_race": "前走からの間隔",
    "weight_change": "馬体重の増減",
    
    # 血統
    "sire_win_rate_for_distance": "父の距離適性",
    "sire_win_rate_for_surface": "父の馬場適性",
    
    # レース条件
    "odds": "単勝オッズ（市場の評価）",
    "weight_carried": "斤量",
    "jockey_win_rate": "騎手の勝率",
}
```

### D-2. 予測モデルの構築

```
predictor/
├── __init__.py
├── logic.py              # 脚質判定（既存）
├── feature_factory.py     # 特徴量生成
├── model.py               # 予測モデル（学習・推論）
├── trainer.py             # モデル訓練スクリプト
└── evaluator.py           # 精度評価
```

**アプローチ**:
1. LightGBM / XGBoost で着順予測（回帰 or ランキング）
2. 勝率・複勝率の確率出力
3. Cross-validationで精度評価
4. 予測結果をシミュレーションに反映

### D-3. 予測APIの拡張

```python
# 新規エンドポイント
POST /api/predict/{race_id}   # レースの着順予測
GET  /api/predict/history      # 予測履歴
GET  /api/predict/accuracy     # 予測精度レポート
```

### D-4. 予測結果のUI表示

- シミュレーション画面に「AI予測」タブ追加
- 予測着順 vs 実際着順の比較表
- 予測精度の推移グラフ

---

## Phase E: テスト・品質保証 🧪

**優先度: 中** | **見積もり: 2〜3日**

### E-1. フロントエンドテストの拡充

**現状の問題**: テストが `simulation/__tests__/` に1ファイルのみ

**改善案**:
```
src/
├── api/__tests__/
│   ├── client.test.ts         # APIクライアントテスト（モック）
│   └── raceApi.test.ts        # レースAPI呼び出しテスト
├── components/__tests__/
│   ├── RaceSelector.test.tsx
│   ├── RankingPanel.test.tsx
│   └── EntryTable.test.tsx
├── simulation/__tests__/
│   ├── SimulationEngine.test.ts
│   ├── PositionCalculator.test.ts
│   └── TrackRenderer.test.ts
└── hooks/__tests__/
    ├── useRaceData.test.ts
    └── useSimulation.test.ts
```

### E-2. E2Eテスト（Playwright）

- レース選択 → シミュレーション実行 → 結果表示の一連のフロー
- レスポンシブ表示の確認
- APIエラー時のグレースフルデグラデーション

### E-3. バックエンドテストの強化

- スクレイパーの統合テスト（実データのスナップショットテスト）
- API負荷テスト
- 予測エンジンのユニットテスト

### E-4. CI/CD パイプライン

```yaml
# GitHub Actions
on: [push, pull_request]
jobs:
  frontend:
    - npm run type-check
    - npm run lint
    - npm test
  backend:
    - ruff check
    - mypy app/
    - pytest tests/ --cov=app --cov-fail-under=80
```

---

## Phase F: 運用・デプロイ基盤 🚀

**優先度: 低（ローカル利用なら不要）** | **見積もり: 2〜3日**

### F-1. Docker化

```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]
```

### F-2. データ管理

- DBマイグレーション（Alembic導入）
- データバックアップ・リストア機能
- スクレイピングのスケジュール実行

### F-3. ログ・モニタリング

- 構造化ログ（structlog）
- APIリクエストログ
- エラー通知

---

## 📊 優先順位マトリクス

| Phase | 影響度 | 工数 | ROI | 推奨順序 |
|-------|--------|------|-----|---------|
| A: 基盤整備 | ⭐⭐⭐⭐ | 2〜3日 | 高 | 🥇 1番目 |
| B: UI/UX刷新 | ⭐⭐⭐⭐⭐ | 3〜5日 | 高 | 🥈 2番目 |
| C: シミュ品質 | ⭐⭐⭐⭐⭐ | 3〜4日 | 高 | 🥉 3番目 |
| D: 予測エンジン | ⭐⭐⭐ | 5〜7日 | 中 | 4番目 |
| E: テスト | ⭐⭐⭐ | 2〜3日 | 中 | 5番目 |
| F: 運用基盤 | ⭐⭐ | 2〜3日 | 低 | 6番目 |

---

## 🎯 推奨: まず最初に着手すべき3つ

### 1. 🔧 RaceSimulator の分割 (A-1)
576行のモノリシックコンポーネントは全ての改善のボトルネック。これを分割することで、以降の改善がスムーズになる。

### 2. 🎮 実データ駆動シミュレーション (C-1) ✅
通過順・走破タイム・着差データを活用し、シミュレーション品質が劇的に向上。（パス）

### 3. 🎨 デザインシステム + ダークモードUI (B-1, B-2)
見た目の印象が大きく変わり、アプリ全体の完成度が上がる。

---

## 📝 次のアクション

この計画について：
1. **優先度の調整**: 特に注力したい領域はありますか？
2. **スコープの確認**: ローカル利用のみなら Phase F は後回しでOK
3. **着手**: 承認いただければ Phase A-1 から実装を開始します
