import { useEffect, useRef, useState } from "react";
import { Application, Container, Graphics, Ticker } from "pixi.js";
import { HorseSprite } from "./models/HorseSprite";
import { raceApi } from "../api/raceApi";
import type { HorseAnalysisResponse, RaceDetailResponse, RaceListItem } from "../types";

import { SIMULATION_CONFIG } from "./config";

const { WIDTH: COURSE_WIDTH, HEIGHT: COURSE_HEIGHT, TRACK_RADIUS, STRAIGHT_LENGTH } = SIMULATION_CONFIG;

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
  const startedRef = useRef(false);
  const updateLogicRef = useRef<((ticker: Ticker) => void) | null>(null);

  useEffect(() => {
    startedRef.current = started;
  }, [started]);

  // レース一覧取得
  useEffect(() => {
    const fetchRaces = async () => {
      try {
        const data = await raceApi.getRaces();
        setRaces(data);
        if (data.length > 0 && !selectedRaceId) {
          setSelectedRaceId(data[0].race_id);
        }
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

  const initializingRef = useRef(false);

  useEffect(() => {
    if (!canvasRef.current || appRef.current || initializingRef.current) return;

    initializingRef.current = true;
    const app = new Application();
    app.init({
      width: COURSE_WIDTH,
      height: COURSE_HEIGHT,
      backgroundColor: 0x2e8b57,
      antialias: true,
      resolution: window.devicePixelRatio || 1,
      autoDensity: true,
    }).then(() => {
      if (canvasRef.current) {
        if (canvasRef.current.hasChildNodes()) {
          canvasRef.current.innerHTML = "";
        }
        canvasRef.current.appendChild(app.canvas);
        appRef.current = app;
        renderSimContent();
      }
      initializingRef.current = false;
    }).catch(err => {
      console.error("Pixi init error", err);
      initializingRef.current = false;
    });

    return () => {
      if (appRef.current) {
        appRef.current.destroy(true, { children: true, texture: true });
        appRef.current = null;
      }
    };
  }, []);

  const renderSimContent = () => {
    const app = appRef.current;
    if (!app) return;

    if (updateLogicRef.current) {
      app.ticker.remove(updateLogicRef.current);
      updateLogicRef.current = null;
    }

    app.stage.removeChildren();

    const centerX = COURSE_WIDTH / 2;
    const centerY = COURSE_HEIGHT / 2;

    const bg = new Graphics();
    bg.rect(0, 0, COURSE_WIDTH, COURSE_HEIGHT);
    bg.fill(0x2e8b57);
    app.stage.addChild(bg);

    const trackLayer = new Container();
    const graphics = new Graphics();
    graphics.moveTo(centerX - STRAIGHT_LENGTH / 2, centerY - TRACK_RADIUS);
    graphics.lineTo(centerX + STRAIGHT_LENGTH / 2, centerY - TRACK_RADIUS);
    graphics.arc(centerX + STRAIGHT_LENGTH / 2, centerY, TRACK_RADIUS, -Math.PI / 2, Math.PI / 2);
    graphics.lineTo(centerX - STRAIGHT_LENGTH / 2, centerY + TRACK_RADIUS);
    graphics.arc(centerX - STRAIGHT_LENGTH / 2, centerY, TRACK_RADIUS, Math.PI / 2, -Math.PI / 2);
    graphics.stroke({ width: 4, color: 0xffffff });

    const outerRadius = TRACK_RADIUS + 80;
    graphics.moveTo(centerX - STRAIGHT_LENGTH / 2, centerY - outerRadius);
    graphics.lineTo(centerX + STRAIGHT_LENGTH / 2, centerY - outerRadius);
    graphics.arc(centerX + STRAIGHT_LENGTH / 2, centerY, outerRadius, -Math.PI / 2, Math.PI / 2);
    graphics.lineTo(centerX - STRAIGHT_LENGTH / 2, centerY + outerRadius);
    graphics.arc(centerX - STRAIGHT_LENGTH / 2, centerY, outerRadius, Math.PI / 2, -Math.PI / 2);
    graphics.stroke({ width: 2, color: 0xffffff });

    graphics.moveTo(centerX, centerY + TRACK_RADIUS);
    graphics.lineTo(centerX, centerY + outerRadius);
    graphics.stroke({ width: 4, color: 0xffff00 });

    trackLayer.addChild(graphics);
    app.stage.addChild(trackLayer);

    const horseLayer = new Container();
    const sprites: HorseSprite[] = [];
    const totalPerimeter = 2 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS;

    if (raceDetail) {
      const targetDistance = raceDetail.distance;
      const startOffset = (totalPerimeter - (targetDistance % totalPerimeter)) % totalPerimeter;

      raceDetail.entries.forEach((entry, i) => {
        const sprite = new HorseSprite(entry.horse_number, entry.bracket_number || 1);
        const d = startOffset % totalPerimeter;
        let x, y;
        if (d < STRAIGHT_LENGTH / 2) {
          x = centerX - d; y = centerY + TRACK_RADIUS + (i * 5);
        } else if (d < STRAIGHT_LENGTH / 2 + Math.PI * TRACK_RADIUS) {
          const theta = Math.PI / 2 + (d - STRAIGHT_LENGTH / 2) / TRACK_RADIUS;
          x = (centerX - STRAIGHT_LENGTH / 2) + Math.cos(theta) * (TRACK_RADIUS + (i * 5));
          y = centerY + Math.sin(theta) * (TRACK_RADIUS + (i * 5));
        } else if (d < 1.5 * STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS) {
          const d2 = d - (STRAIGHT_LENGTH / 2 + Math.PI * TRACK_RADIUS);
          x = (centerX - STRAIGHT_LENGTH / 2) + d2;
          y = centerY - TRACK_RADIUS - (i * 5);
        } else if (d < 1.5 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS) {
          const theta = 1.5 * Math.PI + (d - (1.5 * STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS)) / TRACK_RADIUS;
          x = (centerX + STRAIGHT_LENGTH / 2) + Math.cos(theta) * (TRACK_RADIUS + (i * 5));
          y = centerY + Math.sin(theta) * (TRACK_RADIUS + (i * 5));
        } else {
          const d2 = d - (1.5 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS);
          x = (centerX + STRAIGHT_LENGTH / 2) - d2;
          y = centerY + TRACK_RADIUS + (i * 5);
        }
        sprite.x = x;
        sprite.y = y;
        horseLayer.addChild(sprite);
        sprites.push(sprite);
      });
    }
    app.stage.addChild(horseLayer);
    horsesRef.current = sprites;

    const progress = sprites.map(() => 0);
    const styleFactors = sprites.map((_, i) => {
      const entry = raceDetail?.entries[i];
      const analysis = entry ? horseAnalyses[entry.horse.horse_id] : null;
      const style = analysis?.style || "UNKNOWN";
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
      return 2 + (analysis?.stats.speed || 50) / 100;
    });

    const updateLogic = (ticker: Ticker) => {
      if (!startedRef.current) return;

      const targetDistance = raceDetail?.distance || 1600;
      const startOffset = (totalPerimeter - (targetDistance % totalPerimeter)) % totalPerimeter;
      let allFinished = true;

      sprites.forEach((sprite, i) => {
        if (progress[i] < targetDistance) {
          allFinished = false;
          const currentProgressRatio = progress[i] / targetDistance;
          const phaseFactor = currentProgressRatio < 0.6 ? styleFactors[i].early : styleFactors[i].late;

          const baseSpeed = speeds[i] * 5;
          const speed = baseSpeed * phaseFactor * ticker.deltaTime;
          progress[i] += speed;
        }

        const d = (startOffset + progress[i]) % totalPerimeter;
        let x, y;

        if (d < STRAIGHT_LENGTH / 2) {
          x = centerX - d;
          y = centerY + TRACK_RADIUS + (i * 5);
        } else if (d < STRAIGHT_LENGTH / 2 + Math.PI * TRACK_RADIUS) {
          const theta = Math.PI / 2 + (d - STRAIGHT_LENGTH / 2) / TRACK_RADIUS;
          x = (centerX - STRAIGHT_LENGTH / 2) + Math.cos(theta) * (TRACK_RADIUS + i * 5);
          y = centerY + Math.sin(theta) * (TRACK_RADIUS + i * 5);
        } else if (d < 1.5 * STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS) {
          const d2 = d - (STRAIGHT_LENGTH / 2 + Math.PI * TRACK_RADIUS);
          x = (centerX - STRAIGHT_LENGTH / 2) + d2;
          y = centerY - TRACK_RADIUS - (i * 5);
        } else if (d < 1.5 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS) {
          const theta = 1.5 * Math.PI + (d - (1.5 * STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS)) / TRACK_RADIUS;
          x = (centerX + STRAIGHT_LENGTH / 2) + Math.cos(theta) * (TRACK_RADIUS + i * 5);
          y = centerY + Math.sin(theta) * (TRACK_RADIUS + i * 5);
        } else {
          const d2 = d - (1.5 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS);
          x = (centerX + STRAIGHT_LENGTH / 2) - d2;
          y = centerY + TRACK_RADIUS + (i * 5);
        }

        sprite.x = x;
        sprite.y = y;
      });

      if (allFinished && sprites.length > 0) {
        setStarted(false);
      }
    };

    updateLogicRef.current = updateLogic;
    app.ticker.add(updateLogic);
  };

  useEffect(() => {
    if (appRef.current) {
      renderSimContent();
    }
  }, [raceDetail, horseAnalyses]);

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
            onClick={() => {
              if (started) {
                setStarted(false);
                renderSimContent();
              } else {
                setStarted(true);
              }
            }}
            disabled={!selectedRaceId || loading}
            style={{ padding: "8px 16px", cursor: "pointer", marginRight: "10px" }}
          >
            {started ? "⏹️ ストップ" : "🏁 レース開始"}
          </button>
          <button
            onClick={() => {
              setStarted(false);
              renderSimContent();
            }}
            style={{ padding: "8px 16px", cursor: "pointer" }}
          >
            🔄 リセット
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
