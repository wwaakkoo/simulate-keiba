/**
 * シミュレーションエンジン
 *
 * 馬ごとの進行状態を管理し、Ticker コールバックで毎フレーム更新する。
 * PixiJS の描画層には一切依存せず、「進行距離 → コールバック」で通知する。
 */
import type { Ticker } from "pixi.js";
import type { HorseSetup, OnHorseFinish, OnAllFinish } from "./types";
import { ProbabilisticStrategy } from "./strategies/ProbabilisticStrategy";
import { RealResultStrategy } from "./strategies/RealResultStrategy";
import type { SimulationStrategy } from "./strategies/SimulationStrategy";

export type { HorseSetup, SimResult, OnHorseFinish, OnAllFinish } from "./types";

// ─── シミュレーションエンジン ─────────────────────

export class SimulationEngine {
    private _horses: HorseSetup[];
    private _targetDistance: number;
    private _simSpeed: number;
    private _strategy: SimulationStrategy;

    // 1 頭ごとの走行状態
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

        this._finished = new Set();

        // Strategy Selection
        // If at least one horse has a finish time, we assume this is a past race replay.
        const hasResults = horses.some(h => !!h.entry.finish_time);

        if (hasResults) {
            this._strategy = new RealResultStrategy();
        } else {
            this._strategy = new ProbabilisticStrategy();
        }

        this._strategy.init(horses, targetDistance);
    }

    /** シミュレーション開始 */
    start(): void {
        this._elapsedTime = 0;
    }

    /** 任意の時間(秒)にシーク */
    setTime(time: number): void {
        this._elapsedTime = Math.max(0, time);
        // Force update strategy with 0 delta to sync state
        this._strategy.update(0, this._elapsedTime);

        // Reset finished state if we go back
        if (time === 0) {
            this._finished.clear();
        } else {
            // Re-evaluate finished state for all horses
            for (let i = 0; i < this._horses.length; i++) {
                const dist = this._strategy.getProgress(i);
                if (dist < this._targetDistance) {
                    this._finished.delete(i);
                } else {
                    this._finished.add(i);
                }
            }
        }
    }

    /** シミュレーション速度を動的に変更 */
    setSpeed(speed: number): void {
        this._simSpeed = speed;
    }

    /** 現在の経過時間を返す */
    getTime(): number {
        return this._elapsedTime;
    }

    /** 馬ごとの現在の進行距離を返す */
    getProgress(): number[] {
        // Map current progress from strategy
        return this._horses.map((_, i) => this._strategy.getProgress(i));
    }

    /** 馬ごとの現在の速度(m/s)を返す */
    getSpeeds(): number[] {
        return this._horses.map((_, i) => this._strategy.getSpeed(i));
    }

    /** Ticker のコールバックとして毎フレーム呼び出す */
    update = (ticker: Ticker): void => {
        let allFinished = true;

        // 経過時間を加算 (1frame = 1/60s と仮定)
        // ticker.deltaTime は 60FPS 基準で約 1.0
        const dtFrame = ticker.deltaTime;
        const dtSeconds = (dtFrame / 60) * this._simSpeed; // Simulated seconds passed

        this._elapsedTime += dtSeconds;

        // Update strategy state
        this._strategy.update(dtSeconds, this._elapsedTime);

        for (let i = 0; i < this._horses.length; i++) {
            const currentDist = this._strategy.getProgress(i);

            // Check if finished
            if (currentDist >= this._targetDistance) {
                if (!this._finished.has(i)) {
                    this._finished.add(i);
                    this._onHorseFinish({
                        horseNumber: this._horses[i].horseNumber,
                        time: this._elapsedTime,
                    });
                }
            } else {
                allFinished = false;
            }
        }

        if (allFinished && this._horses.length > 0) {
            this._onAllFinish();
        }
    };
}

