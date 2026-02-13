/**
 * シミュレーション制御ボタン群（速度切替・開始・リセット）
 */

interface SimControlsProps {
    simSpeed: number;
    onSpeedChange: (speed: number) => void;
    onStart: () => void;
    onReset: () => void;
    canStart: boolean;
    running: boolean;
}

const SPEED_OPTIONS = [1, 2, 5] as const;

export const SimControls = ({
    simSpeed,
    onSpeedChange,
    onStart,
    onReset,
    canStart,
    running,
}: SimControlsProps) => (
    <div className="sim-controls">
        {/* 速度切替 */}
        <div className="sim-speed-group">
            {SPEED_OPTIONS.map((v) => (
                <button
                    key={v}
                    onClick={() => onSpeedChange(v)}
                    className={`sim-speed-btn ${simSpeed === v ? "sim-speed-btn--active" : ""}`}
                >
                    {v}x
                </button>
            ))}
        </div>

        {/* 開始ボタン */}
        <button
            onClick={onStart}
            disabled={!canStart || running}
            className={`sim-start-btn ${!canStart || running ? "sim-start-btn--disabled" : ""}`}
        >
            {running ? "🐎 走行中..." : "🏁 レース開始"}
        </button>

        {/* リセットボタン */}
        <button onClick={onReset} className="sim-reset-btn">
            🔄 リセット
        </button>
    </div>
);
