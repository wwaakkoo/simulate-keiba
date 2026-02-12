import { describe, it, expect } from 'vitest';
import { SIMULATION_CONFIG } from '@/simulation';

describe('SIMULATION_CONFIG', () => {
    it('should have valid canvas dimensions', () => {
        expect(SIMULATION_CONFIG.WIDTH).toBeGreaterThan(0);
        expect(SIMULATION_CONFIG.HEIGHT).toBeGreaterThan(0);
    });

    it('should have valid FPS', () => {
        expect(SIMULATION_CONFIG.FPS).toBe(60);
    });

    it('should have default speed multiplier of 1.0', () => {
        expect(SIMULATION_CONFIG.SPEED_MULTIPLIER).toBe(1.0);
    });
});
