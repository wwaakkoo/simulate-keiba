import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { RaceSimulator } from "./simulation";
import "./App.css";

function Home() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>🏇 競馬シミュレーター</h1>
        <p className="app-subtitle">レース予測 & ビジュアルシミュレーション</p>
      </header>
      <main className="app-main">
        <div className="status-card">
          <h2>📊 ステータス</h2>
          <ul className="status-list">
            <li className="status-item status-ok">✅ フロントエンド稼働中</li>
            <li className="status-item status-pending">⏳ バックエンド未接続</li>
            <li className="status-item status-pending">⏳ データベース未構築</li>
            <li className="status-item status-pending">
              ⏳ 予測エンジン未実装
            </li>
          </ul>
        </div>
        <div className="status-card">
          <h2>🗺️ 開発ロードマップ</h2>
          <ol className="roadmap-list">
            <li className="roadmap-item done">
              Phase 0: プロジェクトセットアップ
            </li>
            <li className="roadmap-item done">Phase 1: データ収集基盤</li>
            <li className="roadmap-item done">
              Phase 2: 予測エンジン (API実装済)
            </li>
            <li className="roadmap-item processing">
              Phase 3: レースシミュレーション (実装中)
            </li>
            <li className="roadmap-item">Phase 4: 統合 & UI仕上げ</li>
          </ol>
        </div>

        <div className="action-area" style={{ marginTop: "2rem" }}>
          <Link to="/simulation" className="simulation-link-button">
            🎮 レースシミュレーション画面へ (デモ)
          </Link>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/simulation" element={<RaceSimulator />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
