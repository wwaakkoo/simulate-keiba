import { useEffect, useRef, useState } from "react";
import { Application, Container, Graphics, Ticker } from "pixi.js";
import { HorseSprite } from "./models/HorseSprite";
import { raceApi } from "../api/raceApi";
import type { HorseAnalysisResponse, RaceDetailResponse, RaceListItem } from "../types";

const COURSE_WIDTH = 1000;
const COURSE_HEIGHT = 500;
const TRACK_RADIUS = 150;
const STRAIGHT_LENGTH = 400;

export const RaceSimulator = () => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const horsesRef = useRef<HorseSprite[]>([]);

  const [races, setRaces] = useState<RaceListItem[]>([]);
  const [selectedRaceId, setSelectedRaceId] = useState<string>("");
  const [raceDetail, setRaceDetail] = useState<RaceDetailResponse | null>(null);
  const [horseAnalyses, setHorseAnalyses] = useState<Record<string, HorseAnalysisResponse>>({});
  const [loading, setLoading] = useState(false);
  const [started, setStarted] = useState(false);

  // レース一覧取得
  useEffect(() => {
    const fetchRaces = async () => {
      try {
        const data = await raceApi.getRaces();
        setRaces(data);
        if (data.length > 0) setSelectedRaceId(data[0].race_id);
      } catch (e) {
        console.error("Failed to fetch races:", e);
      }
    };
    fetchRaces();
  }, []);

  // レース詳細と分析データの読込
  const loadRaceData = async (raceId: string) => {
    setLoading(true);
    setStarted(false);
    try {
      const detail = await raceApi.getRaceDetail(raceId);
      setRaceDetail(detail);

      // 全ての馬の分析データを並列取得
      const analyses: Record<string, HorseAnalysisResponse> = {};
      await Promise.all(
        detail.entries.map(async (entry) => {
          try {
            const analysis = await raceApi.getHorseAnalysis(entry.horse.horse_id);
            analyses[entry.horse.horse_id] = analysis;
          } catch (e) {
            console.warn(`Failed to fetch analysis for horse ${entry.horse.horse_id}`, e);
          }
        })
      );
      setHorseAnalyses(analyses);
    } catch (e) {
      console.error("Failed to load race data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedRaceId) {
      loadRaceData(selectedRaceId);
    }
  }, [selectedRaceId]);

  useEffect(() => {
    const initPixi = async () => {
      const app = new Application();
      await app.init({
        width: COURSE_WIDTH,
        height: COURSE_HEIGHT,
        backgroundColor: 0x2e8b57,
        antialias: true,
      });

      if (canvasRef.current && !canvasRef.current.hasChildNodes()) {
        canvasRef.current.appendChild(app.canvas);
      }
      appRef.current = app;

      // 2. オーバルコース描画
      const trackLayer = new Container();
      const graphics = new Graphics();

      const centerX = COURSE_WIDTH / 2;
      const centerY = COURSE_HEIGHT / 2;

      // 内柵
      graphics.moveTo(centerX - STRAIGHT_LENGTH / 2, centerY - TRACK_RADIUS);
      graphics.lineTo(centerX + STRAIGHT_LENGTH / 2, centerY - TRACK_RADIUS);
      graphics.arc(centerX + STRAIGHT_LENGTH / 2, centerY, TRACK_RADIUS, -Math.PI / 2, Math.PI / 2);
      graphics.lineTo(centerX - STRAIGHT_LENGTH / 2, centerY + TRACK_RADIUS);
      graphics.arc(centerX - STRAIGHT_LENGTH / 2, centerY, TRACK_RADIUS, Math.PI / 2, -Math.PI / 2);
      graphics.stroke({ width: 2, color: 0xffffff });

      // 外柵
      const outerRadius = TRACK_RADIUS + 80;
      graphics.moveTo(centerX - STRAIGHT_LENGTH / 2, centerY - outerRadius);
      graphics.lineTo(centerX + STRAIGHT_LENGTH / 2, centerY - outerRadius);
      graphics.arc(centerX + STRAIGHT_LENGTH / 2, centerY, outerRadius, -Math.PI / 2, Math.PI / 2);
      graphics.lineTo(centerX - STRAIGHT_LENGTH / 2, centerY + outerRadius);
      graphics.arc(centerX - STRAIGHT_LENGTH / 2, centerY, outerRadius, Math.PI / 2, -Math.PI / 2);
      graphics.stroke({ width: 2, color: 0xffffff });

      trackLayer.addChild(graphics);
      app.stage.addChild(trackLayer);

      // 3. 馬の配置 (実データ)
      const horseLayer = new Container();
      const sprites: HorseSprite[] = [];

      if (raceDetail) {
        raceDetail.entries.forEach((entry, i) => {
          const sprite = new HorseSprite(entry.horse_number, entry.bracket_number || 1);
          // スタート地点
          sprite.x = centerX + STRAIGHT_LENGTH / 2;
          sprite.y = centerY + TRACK_RADIUS + 10 + i * 5;
          horseLayer.addChild(sprite);
          sprites.push(sprite);
        });
      }

      app.stage.addChild(horseLayer);
      horsesRef.current = sprites;

      // 4. アニメーション
      const progress = sprites.map(() => 0);
      const styleFactors = sprites.map((_, i) => {
        const entry = raceDetail?.entries[i];
        const analysis = entry ? horseAnalyses[entry.horse.horse_id] : null;
        const style = analysis?.style || "UNKNOWN";

        // 脚質ごとの速度特性 (前半/後半の倍率)
        switch (style) {
          case "NIGE": return { early: 1.2, late: 0.8 };
          case "SENKO": return { early: 1.1, late: 0.9 };
          case "SASHI": return { early: 0.9, late: 1.1 };
          case "OIKOMI": return { early: 0.8, late: 1.2 };
          default: return { early: 1.0, late: 1.0 };
        }
      });

      const speeds = sprites.map((_, i) => {
        const entry = raceDetail?.entries[i];
        const analysis = entry ? horseAnalyses[entry.horse.horse_id] : null;
        // 基本速度 + 個別スタッツ (暫定)
        return 2 + (analysis?.stats.speed || 50) / 100;
      });

      app.ticker.add((ticker: Ticker) => {
        if (!started) return;

        const totalPerimeter = 2 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS;

        sprites.forEach((sprite, i) => {
          // レースの進行状況 (0.0 ~ 1.0)
          const currentProgress = progress[i] / totalPerimeter;
          const factors = styleFactors[i];
          const phaseFactor = currentProgress < 0.6 ? factors.early : factors.late;

          const speed = speeds[i] * phaseFactor * ticker.deltaTime;
          progress[i] += speed;

          const d = progress[i] % totalPerimeter;

          let x, y;
          if (d < STRAIGHT_LENGTH) {
            x = (centerX + STRAIGHT_LENGTH / 2) - d;
            y = centerY + TRACK_RADIUS + (i * 5);
          } else if (d < STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS) {
            const theta = (d - STRAIGHT_LENGTH) / TRACK_RADIUS + Math.PI / 2;
            x = (centerX - STRAIGHT_LENGTH / 2) + Math.cos(theta) * (TRACK_RADIUS + i * 5);
            y = centerY + Math.sin(theta) * (TRACK_RADIUS + i * 5);
          } else if (d < 2 * STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS) {
            const d2 = d - (STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS);
            x = (centerX - STRAIGHT_LENGTH / 2) + d2;
            y = centerY - TRACK_RADIUS - (i * 5);
          } else {
            const theta = (d - (2 * STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS)) / TRACK_RADIUS - Math.PI / 2;
            x = (centerX + STRAIGHT_LENGTH / 2) + Math.cos(theta) * (TRACK_RADIUS + i * 5);
            y = centerY + Math.sin(theta) * (TRACK_RADIUS + i * 5);
          }

          sprite.x = x;
          sprite.y = y;
        });
      });
    };

    if (appRef.current) {
      // 既存のステージをクリア
      appRef.current.stage.removeChildren();
    }
    initPixi();
  }, [raceDetail, started]); // raceDetail または started が変わるたびに再初期化（プロトタイプなので）

  return (
    <div className="simulator-container" style={{ padding: "20px" }}>
      <header style={{ marginBottom: "20px" }}>
        <h2>🏇 レースシミュレーション</h2>
        <div className="controls">
          <select
            value={selectedRaceId}
            onChange={(e) => setSelectedRaceId(e.target.value)}
            disabled={loading}
            style={{ padding: "8px", marginRight: "10px" }}
          >
            {races.map(race => (
              <option key={race.race_id} value={race.race_id}>
                {race.date} {race.venue} - {race.name} ({race.distance}m)
              </option>
            ))}
          </select>
          <button
            onClick={() => setStarted(true)}
            disabled={!selectedRaceId || loading || started}
            style={{ padding: "8px 16px", cursor: "pointer", marginRight: "10px" }}
          >
            🏁 レース開始
          </button>
          <button
            onClick={() => setStarted(false)}
            style={{ padding: "8px 16px", cursor: "pointer" }}
          >
            ⏹️ リセット
          </button>
        </div>
        {loading && <p>データを読み込み中...</p>}
      </header>

      <div
        ref={canvasRef}
        style={{
          border: '4px solid #1a1a1a',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          display: 'inline-block',
          backgroundColor: '#2e8b57'
        }}
      />

      <footer style={{ marginTop: "20px", color: "#666" }}>
        <p>※ オーバルコースを実装中。現在はデモ表示です。</p>
      </footer>
    </div>
  );
};
