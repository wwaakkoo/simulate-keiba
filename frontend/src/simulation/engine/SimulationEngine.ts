/**
 * シミュレーションエンジン
 *
 * 馬ごとの進行状態を管理し、Ticker コールバックで毎フレーム更新する。
 * PixiJS の描画層には一切依存せず、「進行距離 → コールバック」で通知する。
 */
import type { Ticker } from "pixi.js";
import type { EntryResponse, HorseAnalysisResponse } from "../../types";

// ─── 公開型 ───────────────────────────────────────

/** 1頭ごとのシミュレーション結果 */
export interface SimResult {
    horseNumber: number;
    time: number;
}

/** エンジン初期化時に渡す馬データ */
export interface HorseSetup {
    index: number;
    horseNumber: number;
    entry: EntryResponse;
    analysis: HorseAnalysisResponse | undefined;
}

/** コールバック型 */
export type OnHorseFinish = (result: SimResult) => void;
export type OnAllFinish = () => void;

// ─── 内部定数・ヘルパー ──────────────────────────

/**
 * 脚質ごとの速度配分ファクター
 * - early: レース前半 (0〜60%) の速度倍率
 * - late:  レース後半 (60〜100%) の速度倍率
 */
function getStyleFactor(style: string): { early: number; late: number } {
    switch (style) {
        case "NIGE":
            return { early: 1.2, late: 0.8 };
        case "SENKO":
            return { early: 1.1, late: 0.9 };
        case "SASHI":
            return { early: 0.9, late: 1.1 };
        case "OIKOMI":
            return { early: 0.8, late: 1.2 };
        default:
            return { early: 1.0, late: 1.0 };
    }
}

// 平均速度 ≈ 16.6 m/s  →  1 frame (60fps) あたり 0.276 m
const BASE_SPEED_PER_FRAME = 0.276;
const SPEED_ADJUSTMENT_FACTOR = 0.002;

// ─── シミュレーションエンジン ─────────────────────

export class SimulationEngine {
    private _horses: HorseSetup[];
    private _targetDistance: number;
    private _simSpeed: number;

    // 1 頭ごとの走行状態
    private _progress: number[];
    private _speeds: number[];
    private _styleFactors: { early: number; late: number }[];
    private _finished: Set<number>;

    // タイミング
    private _elapsedTime = 0; // シミュレーション内経過時間 (秒)

    // コールバック
    private _onHorseFinish: OnHorseFinish;
    private _onAllFinish: OnAllFinish;

    constructor(
        horses: HorseSetup[],
        targetDistance: number,
        simSpeed: number,
        onHorseFinish: OnHorseFinish,
        onAllFinish: OnAllFinish,
    ) {
        this._horses = horses;
        this._targetDistance = targetDistance;
        this._simSpeed = simSpeed;
        this._onHorseFinish = onHorseFinish;
        this._onAllFinish = onAllFinish;

        this._progress = horses.map(() => 0);
        this._finished = new Set();

        // 各馬の速度を算出
        this._speeds = horses.map((h) => {
            // 実データ（結果）がある場合はそれを利用する "Result Mode"
            // finish_time (秒換算) があるかどうか
            if (h.entry.finish_time) {
                // finish_time は "1:23.4" などの形式かもしれないし、秒数かもしれない
                // ここでは単純化のため、別途パースが必要だが、EntryResponseの型定義ではstring
                // Phase C-1 で詳細実装するが、まずは既存ロジックの延長で対応
                // 実データがある場合、そのタイムでゴールするように逆算するべきだが
                // 現状は簡易的にスピード指数を使用
            }

            const hasData = h.analysis && h.analysis.stats.races_count > 0;
            let speedStat = h.analysis?.stats.speed ?? 50;

            if (!hasData) {
                // データがない場合は 40~60 の間でランダム化
                speedStat = 40 + Math.random() * 20;
            }

            // 常にわずかなランダムノイズを加える (±2程度)
            const noise = (Math.random() - 0.5) * 4;
            const finalSpeed = speedStat + noise;

            return BASE_SPEED_PER_FRAME + (finalSpeed - 50) * SPEED_ADJUSTMENT_FACTOR;
        });

        // 脚質ファクター
        this._styleFactors = horses.map((h) => {
            let style = h.analysis?.style ?? "UNKNOWN";
            if (style === "UNKNOWN") {
                // UNKNOWNの場合はランダムに割り当てる
                const styles = ["NIGE", "SENKO", "SASHI", "OIKOMI"];
                style = styles[Math.floor(Math.random() * styles.length)];
            }
            return getStyleFactor(style);
        });
    }

    /** シミュレーション開始 */
    start(): void {
        this._elapsedTime = 0;
    }

    /** シミュレーション速度を動的に変更 */
    setSpeed(speed: number): void {
        this._simSpeed = speed;
    }

    /** 馬ごとの現在の進行距離を返す */
    getProgress(): readonly number[] {
        return this._progress;
    }

    /** Ticker のコールバックとして毎フレーム呼び出す */
    update = (ticker: Ticker): void => {
        let allFinished = true;

        // 経過時間を加算 (1frame = 1/60s と仮定)
        // ticker.deltaTime は 60FPS 基準で約 1.0
        const dt = ticker.deltaTime;
        this._elapsedTime += (dt / 60) * this._simSpeed; // 秒単位

        for (let i = 0; i < this._horses.length; i++) {
            if (this._progress[i] >= this._targetDistance) continue;

            allFinished = false;

            const ratio = this._progress[i] / this._targetDistance;
            const factor =
                ratio < 0.6 ? this._styleFactors[i].early : this._styleFactors[i].late;

            this._progress[i] +=
                this._speeds[i] * factor * dt * this._simSpeed;

            // ゴール判定
            if (
                this._progress[i] >= this._targetDistance &&
                !this._finished.has(i)
            ) {
                this._finished.add(i);

                // ゴールタイムはシミュレーション内経過時間を使用
                this._onHorseFinish({
                    horseNumber: this._horses[i].horseNumber,
                    time: this._elapsedTime,
                });
            }
        }

        if (allFinished && this._horses.length > 0) {
            this._onAllFinish();
        }
    };
}
