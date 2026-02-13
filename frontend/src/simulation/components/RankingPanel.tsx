/**
 * シミュレーション結果順位表
 */
import type { SimResult } from "../engine/SimulationEngine";
import type { EntryResponse } from "../../types";

/** 枠番カラーパレット (1〜8枠) */
const BRACKET_COLORS = [
    "#fff",     // 1枠: 白
    "#1a1a1a",  // 2枠: 黒
    "#ef4444",  // 3枠: 赤
    "#3b82f6",  // 4枠: 青
    "#eab308",  // 5枠: 黄
    "#16a34a",  // 6枠: 緑
    "#ea580c",  // 7枠: 橙
    "#f472b6",  // 8枠: 桃
] as const;

/** 白文字にしない枠番 (白い背景のため) */
const LIGHT_BRACKETS = new Set([1, 5]);

interface RankingPanelProps {
    simResults: SimResult[];
    entries: EntryResponse[];
}

function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, "0")}`;
}

export const RankingPanel = ({ simResults, entries }: RankingPanelProps) => (
    <div className="sim-ranking">
        <h3 className="sim-ranking__title">📊 シミュレーション順位</h3>
        <table className="sim-ranking__table">
            <thead>
                <tr>
                    <th>着順</th>
                    <th>馬番</th>
                    <th>タイム</th>
                    <th>実際</th>
                </tr>
            </thead>
            <tbody>
                {simResults.length === 0 && (
                    <tr>
                        <td colSpan={4} className="sim-ranking__empty">
                            レースを開始すると
                            <br />
                            順位が表示されます
                        </td>
                    </tr>
                )}
                {simResults.map((result, idx) => {
                    const entry = entries.find(
                        (e) => e.horse_number === result.horseNumber,
                    );
                    const bracket = entry?.bracket_number ?? 1;
                    const bgColor = BRACKET_COLORS[bracket - 1] ?? "#cbd5e1";
                    const textColor = LIGHT_BRACKETS.has(bracket) ? "#000" : "#fff";

                    return (
                        <tr key={result.horseNumber} className="sim-ranking__row">
                            <td
                                className={`sim-ranking__position ${idx < 3 ? "sim-ranking__position--top3" : ""}`}
                            >
                                {idx + 1}
                            </td>
                            <td className="sim-ranking__horse">
                                <span
                                    className="sim-ranking__bracket-badge"
                                    style={{ backgroundColor: bgColor, color: textColor }}
                                >
                                    {result.horseNumber}
                                </span>
                                {entry?.horse.name}
                            </td>
                            <td className="sim-ranking__time">{formatTime(result.time)}</td>
                            <td className="sim-ranking__actual">
                                {entry?.finish_position
                                    ? `${entry.finish_position}着`
                                    : "-"}
                            </td>
                        </tr>
                    );
                })}
            </tbody>
        </table>
    </div>
);
