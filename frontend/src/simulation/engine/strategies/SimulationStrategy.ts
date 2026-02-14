
import type { HorseSetup } from "../types";

export interface SimulationStrategy {
    /**
     * Initialize the strategy with horse data.
     */
    init(horses: HorseSetup[], targetDistance: number): void;

    /**
     * Update the simulation state.
     * @param dt Delta time in seconds (simulated time).
     * @param currentTime Total elapsed simulation time in seconds.
     */
    update(dt: number, currentTime: number): void;

    /**
     * Get the current progress (distance in meters) for a specific horse.
     */
    getProgress(horseIndex: number): number;
    getSpeed(horseIndex: number): number;
}
