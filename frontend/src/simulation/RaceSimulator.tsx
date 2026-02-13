/**
 * レースシミュレーション メインコンテナ
 *
 * 責務:
 *   - 状態管理のオーケストレーション
 *   - 子コンポーネントの配置
 *   - PixiJS シーン構築の指揮
 *
 * 描画詳細・走行計算・データ取得は engine / hooks に委譲。
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { Container, Graphics, type Ticker } from "pixi.js";

import { usePixiApp } from "./hooks/usePixiApp";
import { useRaceData } from "./hooks/useRaceData";
import {
  SimulationEngine,
  type SimResult,
  type HorseSetup,
} from "./engine/SimulationEngine";
import {
  getTrackPosition,
  calculateStartOffset,
} from "./engine/PositionCalculator";
import { createTrackLayer } from "./engine/TrackRenderer";
import { HorseSprite } from "./models/HorseSprite";
import { SIMULATION_CONFIG } from "./config";

// UI コンポーネント
import { RaceSelector } from "./components/RaceSelector";
import { SimControls } from "./components/SimControls";
import { RaceInfo } from "./components/RaceInfo";
import { RankingPanel } from "./components/RankingPanel";
import { EntryTable } from "./components/EntryTable";

import "./RaceSimulator.css";

const { WIDTH: COURSE_WIDTH, HEIGHT: COURSE_HEIGHT } = SIMULATION_CONFIG;

// ─── メインコンポーネント ──────────────────────────

export const RaceSimulator = () => {
  const { canvasRef, appRef } = usePixiApp();
  const {
    races,
    selectedRaceId,
    selectRace,
    raceDetail,
    horseAnalyses,
    loading,
  } = useRaceData();

  const [started, setStarted] = useState(false);
  const [simSpeed, setSimSpeed] = useState(2);
  const [simResults, setSimResults] = useState<SimResult[]>([]);

  // Ref: started / simSpeed を Ticker コールバック内で参照するため
  const startedRef = useRef(false);
  const simSpeedRef = useRef(simSpeed);
  const simResultsRef = useRef<SimResult[]>([]);
  const engineRef = useRef<SimulationEngine | null>(null);
  const horsesRef = useRef<HorseSprite[]>([]);
  const tickerCbRef = useRef<((ticker: Ticker) => void) | null>(null);

  // started / simSpeed の Ref 同期
  useEffect(() => {
    startedRef.current = started;
  }, [started]);
  useEffect(() => {
    simSpeedRef.current = simSpeed;
    // 走行中にエンジンの速度も反映
    engineRef.current?.setSpeed(simSpeed);
  }, [simSpeed]);

  // ─── シーン構築 ───────────────────────────────

  const buildScene = useCallback(() => {
    const app = appRef.current;
    if (!app || !raceDetail) return;

    // 既存 Ticker コールバック解除（蓄積防止）
    if (tickerCbRef.current) {
      app.ticker.remove(tickerCbRef.current);
      tickerCbRef.current = null;
    }
    engineRef.current = null;
    app.stage.removeChildren();

    // 背景
    const bg = new Graphics();
    bg.rect(0, 0, COURSE_WIDTH, COURSE_HEIGHT);
    bg.fill(0x2e8b57);
    app.stage.addChild(bg);

    // トラック
    app.stage.addChild(createTrackLayer());

    // 馬スプライトの配置
    const horseLayer = new Container();
    const sprites: HorseSprite[] = [];
    const horseSetups: HorseSetup[] = [];
    const startOffsetM = calculateStartOffset(raceDetail.distance);

    let simIndex = 0;
    for (const entry of raceDetail.entries) {
      if (entry.status !== "result") continue;

      const sprite = new HorseSprite(
        entry.horse_number,
        entry.bracket_number ?? 1,
      );
      const laneOffset = simIndex * 5;
      const pos = getTrackPosition(startOffsetM, laneOffset);
      sprite.x = pos.x;
      sprite.y = pos.y;

      horseLayer.addChild(sprite);
      sprites.push(sprite);

      horseSetups.push({
        index: simIndex,
        horseNumber: entry.horse_number,
        entry,
        analysis: horseAnalyses[entry.horse.horse_id],
      });

      simIndex++;
    }
    app.stage.addChild(horseLayer);
    horsesRef.current = sprites;

    // シミュレーションエンジン（simSpeed は Ref 経由で参照）
    const engine = new SimulationEngine(
      horseSetups,
      raceDetail.distance,
      simSpeedRef.current,
      // onHorseFinish
      (result) => {
        simResultsRef.current = [...simResultsRef.current, result];
        setSimResults([...simResultsRef.current]);
      },
      // onAllFinish
      () => {
        setStarted(false);
      },
    );
    engineRef.current = engine;

    // Ticker コールバック（名前付きで保持 → 確実に remove できる）
    const tickerCb = (ticker: Ticker): void => {
      if (!startedRef.current) return;

      // エンジン更新
      engine.update(ticker);

      // スプライト位置反映（すべてメートル単位）
      const progress = engine.getProgress();
      const targetDist = raceDetail.distance;

      for (let i = 0; i < sprites.length; i++) {
        const distM = Math.min(progress[i], targetDist);
        const posM = startOffsetM + distM;
        const laneOffset = i * 5;
        const pos = getTrackPosition(posM, laneOffset);
        sprites[i].x = pos.x;
        sprites[i].y = pos.y;
      }
    };

    tickerCbRef.current = tickerCb;
    app.ticker.add(tickerCb);
  }, [appRef, raceDetail, horseAnalyses]); // simSpeed を依存から除外

  // raceDetail / horseAnalyses 変更時にシーン再構築
  useEffect(() => {
    if (appRef.current && raceDetail) {
      buildScene();
    }
  }, [buildScene, appRef, raceDetail]);

  // ─── イベントハンドラ ─────────────────────────

  const handleStart = useCallback(() => {
    setSimResults([]);
    simResultsRef.current = [];
    setStarted(true);
    engineRef.current?.start();
  }, []);

  const handleReset = useCallback(() => {
    setStarted(false);
    setSimResults([]);
    simResultsRef.current = [];
    buildScene();
  }, [buildScene]);

  const handleSelectRace = useCallback(
    (raceId: string) => {
      setStarted(false);
      setSimResults([]);
      simResultsRef.current = [];
      selectRace(raceId);
    },
    [selectRace],
  );

  // ─── レンダリング ─────────────────────────────

  return (
    <div className="simulator-page">
      {/* ヘッダー */}
      <header className="sim-header">
        <div>
          <h1 className="sim-header__title">
            🏇 レースシミュレーション{" "}
            <span className="sim-header__badge">Prototype</span>
          </h1>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <RaceSelector
            races={races}
            selectedRaceId={selectedRaceId}
            onSelect={handleSelectRace}
            disabled={loading || started}
          />
          <SimControls
            simSpeed={simSpeed}
            onSpeedChange={setSimSpeed}
            onStart={handleStart}
            onReset={handleReset}
            canStart={!!raceDetail}
            running={started}
          />
        </div>
      </header>

      {/* PixiJS キャンバス */}
      <div
        ref={canvasRef}
        className={`sim-canvas ${!loading && raceDetail ? "" : "sim-canvas--hidden"}`}
      />

      {/* ローディング */}
      {loading && <div className="sim-loading">データを読み込み中...</div>}

      {/* メインコンテンツ */}
      {!loading && raceDetail && (
        <div className="sim-content">
          <div className="sim-content__upper">
            <RaceInfo raceDetail={raceDetail} />
            <RankingPanel
              simResults={simResults}
              entries={raceDetail.entries}
            />
          </div>
          <EntryTable
            entries={raceDetail.entries}
            horseAnalyses={horseAnalyses}
          />
        </div>
      )}
    </div>
  );
};
