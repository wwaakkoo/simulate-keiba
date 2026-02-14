
import type { SimulationStrategy } from "./SimulationStrategy";
import type { HorseSetup } from "../types";

// 平均速度 ≈ 16.6 m/s
const BASE_SPEED_M_S = 16.56;
const SPEED_ADJUSTMENT_FACTOR = 0.12; // 0.002 * 60

/**
 * 脚質ごとの速度配分ファクター
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

export class ProbabilisticStrategy implements SimulationStrategy {
    private _horses: HorseSetup[] = [];
    private _speeds: number[] = [];
    private _styleFactors: { early: number; late: number }[] = [];
    private _progress: number[] = [];
    private _targetDistance: number = 0;

    init(horses: HorseSetup[], targetDistance: number): void {
        this._horses = horses;
        this._targetDistance = targetDistance;
        this._progress = horses.map(() => 0);

        // 各馬の速度を算出 (m/s)
        this._speeds = horses.map((h) => {
            const hasData = h.analysis && h.analysis.stats.races_count > 0;
            let speedStat = h.analysis?.stats.speed ?? 50;

            if (!hasData) {
                speedStat = 40 + Math.random() * 20;
            }

            const noise = (Math.random() - 0.5) * 4;
            const finalSpeed = speedStat + noise;

            return BASE_SPEED_M_S + (finalSpeed - 50) * SPEED_ADJUSTMENT_FACTOR;
        });

        // 脚質ファクター
        this._styleFactors = horses.map((h) => {
            let style = h.analysis?.style ?? "UNKNOWN";
            if (style === "UNKNOWN") {
                const styles = ["NIGE", "SENKO", "SASHI", "OIKOMI"];
                style = styles[Math.floor(Math.random() * styles.length)];
            }
            return getStyleFactor(style);
        });
    }

    update(dt: number, _currentTime: number): void {
        for (let i = 0; i < this._horses.length; i++) {
            if (this._progress[i] >= this._targetDistance) continue;

            const ratio = this._progress[i] / this._targetDistance;
            const factor =
                ratio < 0.6 ? this._styleFactors[i].early : this._styleFactors[i].late;

            // 速度(m/s) * ファクター * 経過時間(s)
            this._progress[i] += this._speeds[i] * factor * dt;
        }
    }

    getProgress(horseIndex: number): number {
        return this._progress[horseIndex];
    }

    getSpeed(horseIndex: number): number {
        return this._speeds[horseIndex] || 0;
    }
}
