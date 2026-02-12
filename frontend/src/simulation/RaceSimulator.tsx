import { useEffect, useRef, useState, useMemo } from "react";
import { Application, Container, Graphics, Ticker } from "pixi.js";
import { HorseSprite } from "./models/HorseSprite";
import { raceApi } from "../api/raceApi";
import type { HorseAnalysisResponse, RaceDetailResponse, RaceListItem } from "../types";

import { SIMULATION_CONFIG } from "./config";

const { WIDTH: COURSE_WIDTH, HEIGHT: COURSE_HEIGHT, TRACK_RADIUS, STRAIGHT_LENGTH } = SIMULATION_CONFIG;

interface SimResult {
  horseNumber: number;
  time: number;
}

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

  // シミュレーション結果管理
  const [simSpeed, setSimSpeed] = useState(2); // デフォルト2倍速（完全にリアルだと長いため）
  const [simResults, setSimResults] = useState<SimResult[]>([]);
  const simResultsRef = useRef<SimResult[]>([]);
  const startTimeRef = useRef<number>(0);

  useEffect(() => {
    startedRef.current = started;
    if (started) {
      startTimeRef.current = performance.now();
    }
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
    setSimResults([]);
    simResultsRef.current = [];
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
        canvasRef.current.appendChild(app.canvas);
        appRef.current = app;
        if (raceDetail) renderSimContent();
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

    // ゴールライン
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

      raceDetail.entries.forEach((entry) => {
        if (entry.status !== "result") return;

        const simIndex = sprites.length;
        const sprite = new HorseSprite(entry.horse_number, entry.bracket_number || 1);
        const d = startOffset % totalPerimeter;
        let x, y;
        if (d < STRAIGHT_LENGTH / 2) {
          x = centerX - d; y = centerY + TRACK_RADIUS + (simIndex * 5);
        } else if (d < STRAIGHT_LENGTH / 2 + Math.PI * TRACK_RADIUS) {
          const theta = Math.PI / 2 + (d - STRAIGHT_LENGTH / 2) / TRACK_RADIUS;
          x = (centerX - STRAIGHT_LENGTH / 2) + Math.cos(theta) * (TRACK_RADIUS + (simIndex * 5));
          y = centerY + Math.sin(theta) * (TRACK_RADIUS + (simIndex * 5));
        } else if (d < 1.5 * STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS) {
          const d2 = d - (STRAIGHT_LENGTH / 2 + Math.PI * TRACK_RADIUS);
          x = (centerX - STRAIGHT_LENGTH / 2) + d2;
          y = centerY - TRACK_RADIUS - (simIndex * 5);
        } else if (d < 1.5 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS) {
          const theta = 1.5 * Math.PI + (d - (1.5 * STRAIGHT_LENGTH + Math.PI * TRACK_RADIUS)) / TRACK_RADIUS;
          x = (centerX + STRAIGHT_LENGTH / 2) + Math.cos(theta) * (TRACK_RADIUS + (simIndex * 5));
          y = centerY + Math.sin(theta) * (TRACK_RADIUS + (simIndex * 5));
        } else {
          const d2 = d - (1.5 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS);
          x = (centerX + STRAIGHT_LENGTH / 2) - d2;
          y = centerY + TRACK_RADIUS + (simIndex * 5);
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
    const finishedMap = new Set<number>();

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

    // 実際の走破タイムに近づけるため、速度計算を調整
    // 1600mを約96秒 (1分36秒) で走るとして、平均速度は約16.6m/s
    // PixiJSのticker.deltaTimeはデフォルトで1 (60fpsの場合)
    // 1フレームあたりの移動距離 = (目標平均速度 / FPS) * 調整係数
    // 16.6m/s / 60fps = 約0.276m/frame
    // 調整係数を導入して、stats.speedが50の場合にこの値に近づける
    const baseSpeedPerFrame = 0.276; // 16.6m/s / 60fps
    const speedAdjustmentFactor = 0.005; // stats.speedの影響度

    const speeds = sprites.map((sprite) => {
      const entry = raceDetail?.entries.find(e => e.horse_number === sprite.horseNumber);
      const analysis = entry ? horseAnalyses[entry.horse.horse_id] : null;
      const horseSpeedStat = analysis?.stats.speed || 50;
      // 基本速度 + (馬のスピード能力 - 平均) * 調整係数
      return baseSpeedPerFrame + (horseSpeedStat - 50) * speedAdjustmentFactor;
    });

    const simSpeedRef = { current: simSpeed };

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

          const speed = speeds[i] * phaseFactor * ticker.deltaTime * simSpeedRef.current;
          progress[i] += speed;

          // ゴール判定
          if (progress[i] >= targetDistance && !finishedMap.has(i)) {
            finishedMap.add(i);
            // 経過時間をシミュレーション速度で割って現実の時間に近づける
            const finishTime = (performance.now() - startTimeRef.current) / 1000 / simSpeedRef.current;
            const horseNumber = raceDetail?.entries[i].horse_number || 0;

            const newResult = { horseNumber, time: finishTime };
            simResultsRef.current = [...simResultsRef.current, newResult];
            setSimResults([...simResultsRef.current]);
          }
        }

        const d = (startOffset + (progress[i] > targetDistance ? targetDistance : progress[i])) % totalPerimeter;
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
  }, [raceDetail, horseAnalyses, simSpeed]); // simSpeedが変更されたら再描画

  // フォーマット用ヘルパー
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, "0")}`;
  };

  const handleStart = () => {
    setSimResults([]);
    simResultsRef.current = [];
    setStarted(true);
  };

  return (
    <div className="simulator-page" style={{ padding: "24px", minHeight: "100vh", backgroundColor: "#f8fafc" }}>
      <header style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "24px", color: "#1e293b", display: "flex", alignItems: "center", gap: "10px" }}>
            🏇 レースシミュレーション <span style={{ fontSize: "14px", fontWeight: "normal", background: "#e2e8f0", padding: "4px 12px", borderRadius: "20px" }}>Prototype</span>
          </h1>
        </div>
        <div className="controls" style={{ display: "flex", gap: "12px" }}>
          <select
            value={selectedRaceId}
            onChange={(e) => setSelectedRaceId(e.target.value)}
            disabled={loading || started}
            style={{ padding: "10px 16px", borderRadius: "8px", border: "1px solid #cbd5e1", outline: "none", backgroundColor: "white" }}
          >
            {races.map(race => (
              <option key={race.race_id} value={race.race_id}>
                [{race.date}] {race.venue} {race.name} ({race.distance}m)
              </option>
            ))}
          </select>
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <div style={{ display: "flex", background: "#f1f5f9", borderRadius: "8px", padding: "4px" }}>
              {[1, 2, 5].map(v => (
                <button
                  key={v}
                  onClick={() => setSimSpeed(v)}
                  style={{
                    padding: "4px 12px",
                    borderRadius: "6px",
                    border: "none",
                    background: simSpeed === v ? "white" : "transparent",
                    boxShadow: simSpeed === v ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                    color: simSpeed === v ? "#2563eb" : "#64748b",
                    fontSize: "13px",
                    fontWeight: simSpeed === v ? "bold" : "normal",
                    cursor: "pointer",
                    transition: "all 0.2s"
                  }}
                >
                  {v}x
                </button>
              ))}
            </div>
            <button
              onClick={handleStart}
              disabled={!raceDetail || started}
              style={{
                padding: "8px 20px",
                background: (!raceDetail || started) ? "#cbd5e1" : "#2563eb",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontWeight: "600",
                cursor: (!raceDetail || started) ? "default" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                transition: "all 0.2s"
              }}
            >
              {started ? "🐎 走行中..." : "🏁 レース開始"}
            </button>
            <button
              onClick={() => {
                setStarted(false);
                setSimResults([]);
                simResultsRef.current = [];
                renderSimContent();
              }}
              style={{ padding: "10px 24px", borderRadius: "8px", border: "1px solid #cbd5e1", backgroundColor: "white", fontWeight: "600", cursor: "pointer" }}
            >
              🔄 リセット
            </button>
          </div>
        </div>
      </header>

      <div
        ref={canvasRef}
        style={{
          display: (!loading && raceDetail) ? "flex" : "none",
          justifyContent: "center",
          borderRadius: "8px",
          overflow: "hidden",
          background: "#2e8b57",
          boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
          padding: "16px",
          margin: "0 auto",
          width: "max-content"
        }}
      />

      {loading && <div style={{ textAlign: "center", padding: "40px", fontSize: "18px", color: "#64748b" }}>データを読み込み中...</div>}

      {!loading && raceDetail && (
        <div style={{ display: "flex", gap: "24px", flexDirection: "column", marginTop: "24px" }}>
          {/* 上段: シミュレーターとランキング */}
          <div style={{ display: "flex", gap: "24px", alignItems: "flex-start" }}>
            {/* シミュレーターの説明（キャンバス自体は上に配置） */}
            <div style={{ flex: "1", background: "white", padding: "20px", borderRadius: "12px", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}>
              <div style={{ color: "#1e293b", fontWeight: "600", marginBottom: "12px", display: "flex", justifyContent: "space-between" }}>
                <span>🚩 {raceDetail.venue} {raceDetail.distance}m {raceDetail.course_type}</span>
                <span style={{ color: "#64748b", fontSize: "14px", fontWeight: "normal" }}>※ 現在のシミュレーション速度は目安です</span>
              </div>
              <p style={{ fontSize: "14px", color: "#64748b", margin: 0 }}>
                オーバルコースでの走行シミュレーションです。脚質（逃げ・差し等）に合わせて速度配分が調整されます。
              </p>
            </div>

            {/* ランキングパネル */}
            <div style={{ width: "380px", background: "white", padding: "20px", borderRadius: "12px", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)", maxHeight: "600px", overflowY: "auto" }}>
              <h3 style={{ marginTop: 0, marginBottom: "16px", fontSize: "18px", borderBottom: "2px solid #f1f5f9", paddingBottom: "8px" }}>📊 シミュレーション順位</h3>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ textAlign: "left", fontSize: "13px", color: "#64748b" }}>
                    <th style={{ padding: "8px" }}>着順</th>
                    <th style={{ padding: "8px" }}>馬番</th>
                    <th style={{ padding: "8px" }}>タイム</th>
                    <th style={{ padding: "8px" }}>実際</th>
                  </tr>
                </thead>
                <tbody>
                  {simResults.length === 0 && (
                    <tr>
                      <td colSpan={4} style={{ textAlign: "center", padding: "32px", color: "#94a3b8" }}>レースを開始すると<br />順位が表示されます</td>
                    </tr>
                  )}
                  {simResults.map((result, idx) => {
                    const entry = raceDetail.entries.find(e => e.horse_number === result.horseNumber);
                    return (
                      <tr key={result.horseNumber} style={{ borderBottom: "1px solid #f1f5f9", animation: "slideIn 0.3s ease-out" }}>
                        <td style={{ padding: "10px 8px", fontWeight: "bold", color: idx < 3 ? "#e11d48" : "#1e293b" }}>{idx + 1}</td>
                        <td style={{ padding: "10px 8px" }}>
                          <span style={{
                            display: "inline-block",
                            width: "24px",
                            height: "24px",
                            borderRadius: "4px",
                            backgroundColor: entry?.bracket_number ? ["#fff", "#1a1a1a", "#ef4444", "#3b82f6", "#eab308", "#16a34a", "#ea580c", "#f472b6"][entry.bracket_number - 1] : "#cbd5e1",
                            color: entry?.bracket_number && [1, 5].includes(entry.bracket_number) ? "#000" : "#fff",
                            textAlign: "center",
                            fontSize: "12px",
                            lineHeight: "24px",
                            marginRight: "8px",
                            border: "1px solid #cbd5e1"
                          }}>
                            {result.horseNumber}
                          </span>
                          {entry?.horse.name}
                        </td>
                        <td style={{ padding: "10px 8px", fontSize: "13px", fontFamily: "monospace" }}>{formatTime(result.time)}</td>
                        <td style={{ padding: "10px 8px", fontSize: "13px", color: "#64748b" }}>
                          {entry?.finish_position ? `${entry.finish_position}着` : '-'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 下段: 出走馬一覧詳細 */}
          <div style={{ background: "white", padding: "24px", borderRadius: "12px", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}>
            <h3 style={{ marginTop: 0, marginBottom: "16px", fontSize: "18px" }}>🏇 出走馬詳細情報</h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", fontSize: "14px", color: "#64748b", borderBottom: "2px solid #f1f5f9" }}>
                  <th style={{ padding: "12px 8px" }}>枠-番</th>
                  <th style={{ padding: "12px 8px" }}>馬名</th>
                  <th style={{ padding: "12px 8px" }}>騎手 / 斤量</th>
                  <th style={{ padding: "12px 8px" }}>脚質予測</th>
                  <th style={{ padding: "12px 8px" }}>単勝オッズ</th>
                  <th style={{ padding: "12px 8px" }}>実際の結果</th>
                </tr>
              </thead>
              <tbody>
                {raceDetail.entries.map((entry) => {
                  const analysis = horseAnalyses[entry.horse.horse_id];
                  return (
                    <tr key={entry.horse_number} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "12px 8px" }}>
                        <span style={{ fontSize: "12px", color: "#64748b", marginRight: "4px" }}>{entry.bracket_number}-</span>
                        <strong style={{ fontSize: "16px" }}>{entry.horse_number}</strong>
                      </td>
                      <td style={{ padding: "12px 8px" }}>
                        <div style={{ fontWeight: "600", color: "#1e293b" }}>{entry.horse.name}</div>
                        <div style={{ fontSize: "12px", color: "#64748b" }}>{entry.horse.sex} / {entry.horse.trainer}</div>
                      </td>
                      <td style={{ padding: "12px 8px", fontSize: "14px" }}>
                        {entry.jockey} / {entry.weight_carried}kg
                      </td>
                      <td style={{ padding: "12px 8px" }}>
                        <span style={{
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "12px",
                          backgroundColor: "#f1f5f9",
                          color: "#475569",
                          fontWeight: "bold"
                        }}>
                          {analysis?.style || "分析中..."}
                        </span>
                      </td>
                      <td style={{ padding: "12px 8px" }}>
                        <div style={{ fontWeight: "bold", color: (entry.popularity || 0) <= 3 ? "#e11d48" : "#1e293b" }}>{entry.odds?.toFixed(1) || "-"}</div>
                        <div style={{ fontSize: "11px", color: "#94a3b8" }}>{entry.popularity}番人気</div>
                      </td>
                      <td style={{ padding: "12px 8px", fontSize: "14px" }}>
                        {entry.status === 'result' ? (
                          entry.finish_position ? (
                            <div style={{ display: "flex", flexDirection: "column" }}>
                              <span style={{ fontWeight: "bold" }}>{entry.finish_position}着</span>
                              <span style={{ fontSize: "12px", color: "#64748b" }}>{entry.finish_time}</span>
                            </div>
                          ) : "未確定"
                        ) : (
                          <span style={{ color: "#ef4444", fontWeight: "bold" }}>
                            {entry.status === 'scratched' ? '取消' : entry.status === 'excluded' ? '除外' : '中止'}
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(10px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
};
