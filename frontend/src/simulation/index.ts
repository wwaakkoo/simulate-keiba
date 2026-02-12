/**
 * レースシミュレーション — エントリーポイント
 *
 * PixiJSを使った2Dレースビジュアライゼーション。
 * Phase 3 で本格的に実装予定。
 */

export const SIMULATION_CONFIG = {
    /** キャンバス幅 */
    WIDTH: 1200,
    /** キャンバス高さ */
    HEIGHT: 600,
    /** フレームレート */
    FPS: 60,
    /** レースアニメーション速度（1.0 = リアルタイム） */
    SPEED_MULTIPLIER: 1.0,
} as const;
