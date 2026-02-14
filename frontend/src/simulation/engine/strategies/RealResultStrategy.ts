
import type { SimulationStrategy } from "./SimulationStrategy";
import type { HorseSetup } from "../types";

interface Keyframe {
    time: number;
    distance: number;
}

export class RealResultStrategy implements SimulationStrategy {
    private _keyframes: Keyframe[][] = [];
    private _currentTime: number = 0;

    // Cache for optimization: remembering the last keyframe index per horse
    private _lastKeyframeIndices: number[] = [];

    init(horses: HorseSetup[], targetDistance: number): void {
        this._lastKeyframeIndices = horses.map(() => 0);

        // 1. Find the "Winner Time" (fastest valid time) to use as baseline
        const validTimes = horses
            .map(h => this.parseTime(h.entry.finish_time))
            .filter((t): t is number => t !== null);

        const winnerTime = validTimes.length > 0 ? Math.min(...validTimes) : 90.0; // Default 1:30

        // 2. Generate keyframes for each horse
        this._keyframes = horses.map(h => this.createKeyframes(h, targetDistance, winnerTime));
    }

    update(_dt: number, currentTime: number): void {
        this._currentTime = currentTime;
    }

    getProgress(horseIndex: number): number {
        const frames = this._keyframes[horseIndex];
        if (!frames || frames.length === 0) return 0;

        const t = this._currentTime;

        // Optimize: Start search from last known index
        let startIndex = this._lastKeyframeIndices[horseIndex];
        // Reset if time went backwards (e.g. replay)
        if (startIndex >= frames.length - 1 || frames[startIndex].time > t) {
            startIndex = 0;
        }

        // Find the segment [i, i+1] where frames[i].time <= t <= frames[i+1].time
        let i = startIndex;
        const len = frames.length;
        while (i < len - 1 && frames[i + 1].time < t) {
            i++;
        }
        this._lastKeyframeIndices[horseIndex] = i;

        // Interpolate
        const p0 = frames[i];
        const p1 = frames[i + 1];

        if (!p1) return p0.distance; // End of race

        if (t < p0.time) return p0.distance; // Should not happen usually
        if (t >= p1.time) return p1.distance;

        // 3次スプライン補間 (Catmull-Rom like) or Simple Cubic Ease-in/out
        // 直線補間だとカクつくので、少なくともEaseInOutを使う
        const ratio = (t - p0.time) / (p1.time - p0.time);
        const eased = this.easeInOutQuad(ratio);

        return p0.distance + (p1.distance - p0.distance) * eased;
    }

    private easeInOutQuad(t: number): number {
        return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    }

    getSpeed(horseIndex: number): number {
        const frames = this._keyframes[horseIndex];
        if (!frames || frames.length === 0) return 0;

        const i = this._lastKeyframeIndices[horseIndex];
        const p0 = frames[i];
        const p1 = frames[i + 1];

        if (!p1) return 0; // End of race or single frame
        if (p1.time === p0.time) return 0; // Avoid division by zero

        // 速度の変化も滑らかにするために微分近似
        // v = d(dist)/dt
        // Simple linear speed for now, maybe sufficient
        // Or if we use easeInOutQuad, the derivative is:
        // t < 0.5: 4t
        // t >= 0.5: 4 - 4t
        // multiplied by (distDiff / timeDiff)
        const dt = p1.time - p0.time;
        const dd = p1.distance - p0.distance;
        const baseSpeed = dd / dt;

        // Improve visual speed if we use Easing
        const tRel = (this._currentTime - p0.time) / dt;
        if (tRel < 0 || tRel > 1) return 0; // Out of bounds

        let slope = 1.0;
        if (tRel < 0.5) {
            slope = 4 * tRel;
        } else {
            slope = 4 - 4 * tRel;
        }

        // 完全なEaseInOutだと速度が0から始まり0で終わるため、
        // レース中の「巡航速度」としては不自然になる場合がある。
        // コーナー通過などのキーフレーム間は「等速に近い」ほうが自然かもしれない。
        // いったん「線形補間」に戻して様子を見るか、
        // 「キーフレーム前後での速度連続性」を保つロジックが必要。
        // Current implementation: Just return Average Speed in segment for robustness.
        return baseSpeed;
    }

    private createKeyframes(horse: HorseSetup, targetDistance: number, winnerTime: number): Keyframe[] {
        const frames: Keyframe[] = [];

        // --- 1. Start ---
        frames.push({ time: 0, distance: 0 });

        // --- Data Retrieval ---
        const finishTime = this.parseTime(horse.entry.finish_time);
        const last3F = horse.entry.last_3f; // seconds
        const passingOrder = this.parsePassingOrder(horse.entry.passing_order);

        // 着差 (margin) は今回簡易化のため割愛（finish_timeがあればそれが正確なので）
        // finish_time がない場合はシミュレーション対象外（DNF）
        if (!finishTime) {
            // ゴールしない
            return [{ time: 0, distance: 0 }, { time: 999, distance: 0 }];
        }

        // --- 2. Build Checkpoints ---

        // A. 通過順 (Passing Order) からコーナー位置の時刻を推定
        // 例: "3-3-2-1" (4コーナー)
        // コーナーの位置関係（距離）を定義
        // 日本の競馬場は通常 4コーナー + 直線。
        // 第1コーナー: 全体の approx 20%
        // 第2コーナー: 全体の approx 40%
        // 第3コーナー: 全体の approx 60%
        // 第4コーナー: 全体の approx 80% (残り直線がLast 3Fに近い)

        // 実際にはコース距離によって変わるが、簡易的に等分 + 直線とする
        // passingOrderの要素数に合わせてチェックポイントを作る

        if (passingOrder.length > 0) {
            // コーナーごとの距離 (目安)
            // 4つある場合: 20%, 40%, 60%, 80%
            // 3つある場合: 30%, 60%, 80% ... 適当に配分
            const segmentCount = passingOrder.length + 1; // +1 for Finish

            passingOrder.forEach((rank, index) => {
                // コーナー位置
                // Last 3F (600m) より手前である必要がある
                // 第4コーナー(最後の要素) は Last 3F 地点に近いことが多い

                // 簡易ロジック:
                // インデックス / (要素数) * (Total - Last3F_Dist)
                // しかし Last3F がない場合もある。

                // 単純化: ゴールまでの距離を分割する
                // 第4コーナーは「残り600m～400m」地点
                const remainingDist = targetDistance * (1.0 - (index + 1) / (passingOrder.length + 1));
                const cornerDist = targetDistance - remainingDist;

                // 時刻の推定
                // 基準タイム = (この距離 / 全距離) * 優勝タイム
                const baseReasonableTime = (cornerDist / targetDistance) * winnerTime;

                // 順位による遅れ
                // 1位との差: 1馬身 = 約0.16秒 (0.1s - 0.2s)
                // 単純に (Rank - 1) * 0.1秒 加算
                // 先頭集団のペースにもよるが、簡易シミュとしては十分
                const delay = (rank - 1) * 0.08 + (Math.random() * 0.05);

                let estimatedTime = baseReasonableTime + delay;

                // 前のキーフレームより後であることを保証
                const prevFrame = frames[frames.length - 1];
                if (estimatedTime <= prevFrame.time) {
                    estimatedTime = prevFrame.time + 1.0;
                }

                frames.push({ time: estimatedTime, distance: cornerDist });
            });
        }

        // B. Last 3F (上がり3ハロン)
        // ゴール手前600m地点
        if (last3F && last3F > 0 && targetDistance > 800) {
            const last3FDist = targetDistance - 600;
            const last3FStartTime = finishTime - last3F;

            // 既存のLatestキーフレームと比較
            const prevFrame = frames[frames.length - 1];

            // Last3F地点を追加 (既存より後ろの場合のみ)
            if (prevFrame.distance < last3FDist) {
                // 時間整合性チェック
                let validStartTime = last3FStartTime;
                if (validStartTime <= prevFrame.time) {
                    // おかしい場合は補正（前の地点から巡航速度で来たとするなど）
                    validStartTime = (finishTime + prevFrame.time) / 2;
                }
                frames.push({ time: validStartTime, distance: last3FDist });
            }
            else if (prevFrame.distance > last3FDist) {
                // すでにLast3Fを超えているポイントがあるなら、
                // そのポイントの時刻を再調整するか、無視する
                // ここでは無視して「ゴールタイム」に合わせる
            }
        }

        // --- 3. Finish ---
        // 必ず実際のFinishTimeに到達させる
        const prev = frames[frames.length - 1];
        if (finishTime <= prev.time) {
            // 矛盾がある場合はFinishTimeを優先し、直前のフレームを削除/調整するなどの処理が必要だが
            // ここでは単純に push (getProgressでsort or search対応が必要だが、searchはsort前提)
            // 配列を作り直す
            // ただし今回は簡易的に「FinishTimeは絶対」とするため、
            // 直前がFinishより遅いなら削除する強引な修正
            while (frames.length > 0 && frames[frames.length - 1].time >= finishTime) {
                frames.pop();
            }
            frames.push({ time: 0, distance: 0 }); // 万が一全部消えた場合
        }

        frames.push({ time: finishTime, distance: targetDistance });

        // Sort just in case logic messed up order
        frames.sort((a, b) => a.time - b.time);

        return frames;
    }

    private parseTime(timeStr: string | undefined): number | null {
        if (!timeStr || timeStr === "---") return null;
        try {
            if (timeStr.includes(":")) {
                const [min, sec] = timeStr.split(":");
                // example 1:32.4
                return parseInt(min, 10) * 60 + parseFloat(sec);
            }
            return parseFloat(timeStr);
        } catch {
            return null;
        }
    }

    private parsePassingOrder(orderStr: string | undefined): number[] {
        if (!orderStr) return [];
        // "3-3-2-1" -> [3, 3, 2, 1]
        return orderStr.split("-").map(Number).filter(n => !isNaN(n));
    }
}
