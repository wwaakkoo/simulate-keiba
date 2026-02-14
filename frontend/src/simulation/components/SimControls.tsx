/**
 * シミュレーション制御ボタン群
 *  - 再生/一時停止
 *  - シークバー (プログレス)
 *  - 速度変更
 *  - リセット
 */

interface SimControlsProps {
    currentTime: number;
    duration: number; // 推定最大時間 (秒)
    simSpeed: number;
    isPlaying: boolean;
    onSpeedChange: (speed: number) => void;
    onTogglePlay: () => void;
    onSeek: (time: number) => void;
    onReset: () => void;
    canStart: boolean;
}

const SPEED_OPTIONS = [0.5, 1, 2, 5] as const;

function formatTime(sec: number): string {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 10);
    return `${m}:${s.toString().padStart(2, '0')}.${ms}`;
}

export const SimControls = ({
    currentTime,
    duration,
    simSpeed,
    isPlaying,
    onSpeedChange,
    onTogglePlay,
    onSeek,
    onReset,
    canStart,
}: SimControlsProps) => {

    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
        onSeek(Number(e.target.value));
    };

    return (
        <div className="sim-controls-container">
            {/* 上段: プログレスバー & タイム表示 */}
            <div className="sim-progress-row">
                <span className="sim-time-display">
                    {formatTime(currentTime)} / {formatTime(duration)}
                </span>
                <input
                    type="range"
                    min="0"
                    max={duration}
                    step="0.1"
                    value={currentTime}
                    onChange={handleSeek}
                    className="sim-seek-range"
                    disabled={!canStart}
                />
            </div>

            {/* 下段: コントロールボタン群 */}
            <div className="sim-controls-row">

                {/* 再生/一時停止 */}
                <button
                    onClick={onTogglePlay}
                    disabled={!canStart}
                    className="sim-play-btn"
                >
                    {isPlaying ? "⏸" : "▶"}
                </button>

                {/* リセット(最初に戻る) */}
                <button onClick={onReset} className="sim-reset-btn" disabled={!canStart}>
                    ⏮
                </button>

                <div className="sim-divider" />

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
            </div>
        </div>
    );
};

