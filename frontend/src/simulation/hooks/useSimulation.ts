import { useState, useCallback, useRef } from "react";
import type { SimulationEngine } from "../engine/SimulationEngine";

export interface UseSimulationReturn {
    // State
    elapsedTime: number;
    duration: number; // Estimated duration (or max time)
    isPlaying: boolean;
    playbackSpeed: number;

    // Actions
    play: () => void;
    pause: () => void;
    togglePlay: () => void;
    seek: (time: number) => void;
    setSpeed: (speed: number) => void;
    setElapsedTime: (time: number) => void;

    // Engine Ref (to be set by consumer)
    engineRef: React.MutableRefObject<SimulationEngine | null>;
}

export function useSimulation(): UseSimulationReturn {
    const [elapsedTime, setElapsedTime] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [playbackSpeed, setPlaybackSpeed] = useState(1.0);

    // The engine instance is managed by the consumer (RaceSimulator),
    // but we need a reference to control it.
    const engineRef = useRef<SimulationEngine | null>(null);

    const play = useCallback(() => {
        setIsPlaying(true);
    }, []);

    const pause = useCallback(() => {
        setIsPlaying(false);
    }, []);

    const togglePlay = useCallback(() => {
        setIsPlaying(prev => !prev);
    }, []);

    const seek = useCallback((time: number) => {
        if (engineRef.current) {
            engineRef.current.setTime(time);
            setElapsedTime(time);
        }
    }, []);

    const setSpeed = useCallback((speed: number) => {
        setPlaybackSpeed(speed);
        if (engineRef.current) {
            engineRef.current.setSpeed(speed);
        }
    }, []);

    // NOTE: elapsedTime update is usually driven by the Ticker loop 
    // in the consumer component, which calls engine.update().
    // We need a way to sync engine time to this local state for UI updates (progress bar).
    // This hook assumes the consumer will update `elapsedTime` state via `setElapsedTime`
    // inside the ticker loop, OR we provide a helper to do so.

    // For now, we just expose the state and let RaceSimulator handle the loop.

    return {
        elapsedTime,
        duration: 200, // Temporary default
        isPlaying,
        playbackSpeed,
        play,
        pause,
        togglePlay,
        seek,
        setSpeed,
        setElapsedTime, // Expose for sync
        engineRef
    };
}
