import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>🏇 競馬シミュレーター</h1>
        <p className="app-subtitle">レース予測 &amp; ビジュアルシミュレーション</p>
      </header>
      <main className="app-main">
        <div className="status-card">
          <h2>📊 ステータス</h2>
          <ul className="status-list">
            <li className="status-item status-ok">✅ フロントエンド稼働中</li>
            <li className="status-item status-pending">⏳ バックエンド未接続</li>
            <li className="status-item status-pending">⏳ データベース未構築</li>
            <li className="status-item status-pending">⏳ 予測エンジン未実装</li>
          </ul>
        </div>
        <div className="status-card">
          <h2>🗺️ 開発ロードマップ</h2>
          <ol className="roadmap-list">
            <li className="roadmap-item done">Phase 0: プロジェクトセットアップ</li>
            <li className="roadmap-item">Phase 1: データ収集基盤</li>
            <li className="roadmap-item">Phase 2: 予測エンジン</li>
            <li className="roadmap-item">Phase 3: レースシミュレーション</li>
            <li className="roadmap-item">Phase 4: 統合 &amp; UI仕上げ</li>
          </ol>
        </div>
      </main>
    </div>
  );
}

export default App;
