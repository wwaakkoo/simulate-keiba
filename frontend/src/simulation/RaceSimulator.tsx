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
import { useSimulation } from "./hooks/useSimulation";
import {
  SimulationEngine,
  type SimResult,
  type HorseSetup,
} from "./engine/SimulationEngine";
import {
  getTrackPosition,
  getTrackRotation,
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

  // シミュレーション制御フック
  const {
    elapsedTime,
    duration,
    isPlaying,
    playbackSpeed,
    play,
    pause,
    togglePlay,
    seek,
    setSpeed,
    engineRef,
    setElapsedTime // useSimulation から setElapsedTime を返すように修正済みと仮定
  } = useSimulation();

  const [simResults, setSimResults] = useState<SimResult[]>([]);

  // Ref: Ticker コールバック内で参照するため
  const simResultsRef = useRef<SimResult[]>([]);
  const horsesRef = useRef<HorseSprite[]>([]);
  // tickerCbRef は新しい ticker 管理ロジックでは不要になるが、一旦残す
  const tickerCbRef = useRef<((ticker: Ticker) => void) | null>(null);

  // onSpeedChange wrapper
  const handleSpeedChange = useCallback((speed: number) => {
    setSpeed(speed);
  }, [setSpeed]);

  // ─── シーン構築 ───────────────────────────────

  // isPlaying の Ref 同期
  const isPlayingRef = useRef(isPlaying);
  useEffect(() => {
    isPlayingRef.current = isPlaying;
  }, [isPlaying]);

  // ─── シーン構築 ───────────────────────────────

  const buildScene = useCallback(() => {
    const app = appRef.current;
    if (!app || !raceDetail) return;

    // 既存 Ticker コールバック解除は新しい useEffect で管理するため不要
    // if (tickerCbRef.current) {
    //   app.ticker.remove(tickerCbRef.current);
    //   tickerCbRef.current = null;
    // }
    engineRef.current = null;
    app.stage.removeChildren();

    // 背景
    const bg = new Graphics();
    bg.rect(0, 0, COURSE_WIDTH, COURSE_HEIGHT);
    bg.fill(0x2e8b57);
    app.stage.addChild(bg);

    // トラック
    app.stage.addChild(createTrackLayer(raceDetail.course_type));

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
      // 初期回転 (右向き=0)
      sprite.rotation = 0;

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

    // シミュレーションエンジン
    // スピードは engine.setSpeed() で同期されるので初期値だけでOK
    const engine = new SimulationEngine(
      horseSetups,
      raceDetail.distance,
      playbackSpeed, // useSimulation から取得
      // onHorseFinish
      (result) => {
        simResultsRef.current = [...simResultsRef.current, result];
        setSimResults([...simResultsRef.current]);
      },
      // onAllFinish
      () => {
        pause(); // 自動停止
      },
    );
    engineRef.current = engine;

  }, [appRef, raceDetail, horseAnalyses, pause, playbackSpeed, engineRef]);

  // Ticker 登録/更新
  useEffect(() => {
    const app = appRef.current;
    if (!app) return;

    // Ticker Logic
    const fn = (ticker: Ticker) => {
      const engine = engineRef.current;
      if (!engine || !isPlayingRef.current) return; // isPlayingRef を参照

      engine.update(ticker);

      // スプライト更新
      const progress = engine.getProgress();
      const speeds = engine.getSpeeds();
      const targetDist = raceDetail?.distance || 2000;
      const startOffsetM = raceDetail ? calculateStartOffset(raceDetail.distance) : 0;

      const sprites = horsesRef.current;
      for (let i = 0; i < sprites.length; i++) {
        const distM = Math.min(progress[i], targetDist);
        const posM = startOffsetM + distM;
        const laneOffset = i * 5;

        const pos = getTrackPosition(posM, laneOffset);
        const rot = getTrackRotation(posM); // 回転

        sprites[i].x = pos.x;
        sprites[i].y = pos.y;
        sprites[i].rotation = rot;

        sprites[i].update(ticker.deltaTime, speeds[i]);
      }

      // 時間同期 (注意: ここで setElapsedTime を呼ぶと毎フレーム再描画)
      // パフォーマンス的に間引くのが良い
      // useSimulation の setElapsedTime を使って時間を同期
      if (ticker.deltaMS > 0 && ticker.lastTime % 10 < 1) { // 約100msごとに更新
        setElapsedTime(engine.getTime());
      }
    };

    app.ticker.add(fn);
    return () => { app.ticker.remove(fn); };
  }, [appRef, raceDetail, engineRef, setElapsedTime]);

  // raceDetail 変更時にシーン再構築
  useEffect(() => {
    if (appRef.current && raceDetail) {
      buildScene();
    }
  }, [buildScene, appRef, raceDetail]);

  // ─── イベントハンドラ ─────────────────────────

  const handleSelectRace = useCallback(
    (raceId: string) => {
      pause();
      seek(0);
      setSimResults([]);
      simResultsRef.current = [];
      selectRace(raceId);
    },
    [selectRace, pause, seek],
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
            disabled={loading || isPlaying}
          />
          <SimControls
            currentTime={elapsedTime}
            duration={duration}
            simSpeed={playbackSpeed}
            isPlaying={isPlaying}
            onSpeedChange={handleSpeedChange}
            onTogglePlay={togglePlay}
            onSeek={seek}
            onReset={() => {
              pause();
              seek(0);
              setSimResults([]);
              simResultsRef.current = [];
              buildScene(); // シーンを再構築して初期状態に戻す
            }}
            canStart={!!raceDetail}
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
