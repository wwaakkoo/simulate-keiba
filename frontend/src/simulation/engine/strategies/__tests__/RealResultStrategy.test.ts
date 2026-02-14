
import { describe, it, expect } from "vitest";
import { RealResultStrategy } from "../RealResultStrategy";
import type { HorseSetup } from "../../types";

describe("RealResultStrategy", () => {
    // Helper to create a dummy entry
    const createHorse = (finishTime: string | undefined, passingOrder: string | undefined, last3F?: number): HorseSetup => ({
        index: 0,
        horseNumber: 1,
        entry: {
            horse_number: 1,
            finish_time: finishTime,
            passing_order: passingOrder,
            last_3f: last3F,
            status: "result",
            horse: { horse_id: "1", name: "Test Horse" }
        },
        analysis: undefined
    });

    it("should handle simple finish time", () => {
        const strategy = new RealResultStrategy();
        const horse = createHorse("1:00.0", undefined); // 60s
        strategy.init([horse], 1000);

        strategy.update(0, 0);
        expect(strategy.getProgress(0)).toBe(0);

        strategy.update(0, 30); // Halfway
        expect(strategy.getProgress(0)).toBeCloseTo(500);

        strategy.update(0, 60); // Finish
        expect(strategy.getProgress(0)).toBeCloseTo(1000);
    });

    it("should handle parsing M:SS.T format", () => {
        const strategy = new RealResultStrategy();
        // 1:30.0 = 90s. 1800m.
        const horse = createHorse("1:30.0", undefined);
        strategy.init([horse], 1800);

        strategy.update(0, 45); // Halfway
        expect(strategy.getProgress(0)).toBeCloseTo(900);
    });

    it("should use Last 3F anchor correctly", () => {
        const strategy = new RealResultStrategy();
        // Finish: 100s. Last 3F: 35s. Distance: 2000m.
        // Anchor: 
        //   t=100-35=65s, d=2000-600=1400m
        const horse = createHorse("1:40.0", undefined, 35.0);
        strategy.init([horse], 2000);

        // At t=65, should be at 1400m
        strategy.update(0, 65);
        expect(strategy.getProgress(0)).toBeCloseTo(1400);

        // At t=0 to 65: Speed = 1400 / 65 = 21.53 m/s
        strategy.update(0, 32.5);
        expect(strategy.getProgress(0)).toBeCloseTo(700);

        // At t=65 to 100: Speed = 600 / 35 = 17.14 m/s (Slowing down? weird but consistent with data)
        strategy.update(0, 65 + 17.5); // Halfway through last leg
        expect(strategy.getProgress(0)).toBeCloseTo(1400 + 300);
    });

    it("should handle passing order adjustment (First Corner)", () => {
        const strategy = new RealResultStrategy();
        // Distance 2000m. Winner Time assumed 120s.
        // Horse 1: Finish 120s. Passing "1-1-1-1".
        // Horse 2: Finish 120s. Passing "10-10-10-1".

        const h1 = createHorse("2:00.0", "1-1-1-1", 34.0); // 120s
        const h2 = createHorse("2:00.0", "10-10-10-1", 33.0); // 120s, fast finish

        // We need to Mock the winner time calculation or pass multiple horses
        // If we pass both, min time is 120s.
        strategy.init([h1, h2], 2000);

        // Check early race (e.g. 10% or 20% distance)
        // 20% of 2000m = 400m.
        // H1 should be ahead of H2.

        // Exact time check is hard because the logic involves "WinnerTime * 0.2 + (Rank-1)*0.1"
        // WinnerTime = 120s. BaseTime at 400m (20%) = 24s.
        // H1 Rank 1: Time = 24 + 0 = 24s.
        // H2 Rank 10: Time = 24 + 0.9 = 24.9s.
        // So at T=24s:
        // H1 should be at 400m.
        // H2 should be slightly behind 400m (because it takes 24.9s to get there).

        strategy.update(0, 24.0);
        const p1 = strategy.getProgress(0);
        const p2 = strategy.getProgress(1);

        expect(p1).toBeGreaterThan(p2);
        expect(p1).toBeCloseTo(400, 1);
    });
});
