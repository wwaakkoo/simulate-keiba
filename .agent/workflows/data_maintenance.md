---
description: データ収集とメンテナンス手順
---

# データメンテナンス (simulate-keiba)

## 1. データの新規収集
特定の開催日のレース結果を一括で収集します。
- **エンドポイント**: `POST /api/scrape`
- **引数**: `{"date": "YYYYMMDD"}`
- **CLI (curl)**:
  ```bash
  curl -X POST http://localhost:8000/api/scrape -H "Content-Type: application/json" -d '{"date": "20241222"}'
  ```

## 2. 単一レースのデータ更新
特定のレースIDのデータを再取得または新規取得します。
- **エンドポイント**: `POST /api/scrape/race`
- **引数**: `{"race_id": "202406050811"}`

## 3. 馬の履歴データの蓄積
馬の分析精度が低い場合、プロフィールページから過去データを自動または手動で取得します。
- **自動**: シミュレーション画面で馬を選択した際、履歴が1件以下なら自動でバックグラウンド実行されます。
- **手動 (開発時)**: `ScraperService.scrape_horse_history(horse_id)` を呼び出すスクリプトを実行。

## 4. データベースのクリーンアップ
`data/keiba.db` は SQLite 形式です。直接操作する場合は `check_db.py` などのツールを使用してください。
