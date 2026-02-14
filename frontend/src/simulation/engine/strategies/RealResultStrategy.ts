
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

        const ratio = (t - p0.time) / (p1.time - p0.time);
        return p0.distance + (p1.distance - p0.distance) * ratio;
    }

    getSpeed(horseIndex: number): number {
        const frames = this._keyframes[horseIndex];
        if (!frames || frames.length === 0) return 0;

        const i = this._lastKeyframeIndices[horseIndex];
        const p0 = frames[i];
        const p1 = frames[i + 1];

        if (!p1) return 0; // End of race or single frame
        if (p1.time === p0.time) return 0; // Avoid division by zero

        // Linear speed in this segment
        return (p1.distance - p0.distance) / (p1.time - p0.time);
    }

    private createKeyframes(horse: HorseSetup, targetDistance: number, winnerTime: number): Keyframe[] {
        const frames: Keyframe[] = [];

        // --- 1. Start ---
        frames.push({ time: 0, distance: 0 });

        // --- Data Retrieval ---
        const finishTime = this.parseTime(horse.entry.finish_time);
        const last3F = horse.entry.last_3f; // seconds
        const passingOrder = this.parsePassingOrder(horse.entry.passing_order);

        // If no finish time (DNF etc), horse stays at 0 or moves slowly then stops?
        // Let's make valid entries finish, invalid ones stop.
        if (!finishTime) {
            return [{ time: 0, distance: 0 }, { time: 999, distance: 0 }];
        }

        // --- 2. Intermediate Points ---

        // Strategy: 
        // A. If we have Last 3F, that's a strong anchor.
        //    Point: (Time = FinishTime - Last3F, Distance = Target - 600m)
        if (last3F && last3F > 0 && targetDistance > 600) {
            const last3FDist = targetDistance - 600;
            const last3FTime = finishTime - last3F;

            // Add Passing Order refinement BEFORE Last 3F
            // E.g. First corner at 20% distance
            if (passingOrder.length > 0) {
                const firstCornerDist = targetDistance * 0.2;
                if (firstCornerDist < last3FDist) {
                    const rank = passingOrder[0];
                    // Estimate time: Winner's base time + delay
                    // Base time for 20% distance? Assume constant pace for winner.
                    const winnerPace = winnerTime / targetDistance;
                    const baseTime = winnerPace * firstCornerDist;
                    const delay = (rank - 1) * 0.1; // 0.1s per rank gap

                    // Enforce monotonicity
                    let cornerTime = baseTime + delay;
                    if (cornerTime >= last3FTime) cornerTime = last3FTime * 0.5;

                    frames.push({ time: cornerTime, distance: firstCornerDist });
                }
            }

            // Add Last 3F Anchor
            // Ensure time is increasing
            if (frames[frames.length - 1].time < last3FTime) {
                frames.push({ time: last3FTime, distance: last3FDist });
            }
        }
        else {
            // No Last 3F data. Use passing order to create a middleware point?
            if (passingOrder.length > 0) {
                const midDist = targetDistance * 0.5;
                // Use "average" rank from passing order
                const avgRank = passingOrder.reduce((a, b) => a + b, 0) / passingOrder.length;
                const baseTime = (winnerTime / 2);
                const delay = (avgRank - 1) * 0.15;

                let midTime = baseTime + delay;
                if (midTime >= finishTime) midTime = finishTime * 0.9;

                frames.push({ time: midTime, distance: midDist });
            }
        }

        // --- 3. Finish ---
        frames.push({ time: finishTime, distance: targetDistance });

        // --- 4. Post-Finish ---
        // Keep moving slightly or stop?
        // Ideally stop, but for "run-off" visuals maybe move? 
        // The engine clamps process to targetDistance if finished? 
        // Actually SimulationEngine.update check: if (progress >= targetDistance) continue;
        // So the curve just needs to reach target.

        return frames;
    }

    private parseTime(timeStr: string | undefined): number | null {
        if (!timeStr || timeStr === "---") return null;
        try {
            if (timeStr.includes(":")) {
                const [min, sec] = timeStr.split(":");
                return parseInt(min, 10) * 60 + parseFloat(sec);
            }
            return parseFloat(timeStr);
        } catch {
            return null;
        }
    }

    private parsePassingOrder(orderStr: string | undefined): number[] {
        if (!orderStr) return [];
        return orderStr.split("-").map(Number).filter(n => !isNaN(n));
    }
}
