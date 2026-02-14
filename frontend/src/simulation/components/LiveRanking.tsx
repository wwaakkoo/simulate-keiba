import type { EntryResponse } from "../../types";

interface LiveRankingProps {
    entries: EntryResponse[];
    progress: number[]; // Distances for each horse index
    totalDistance: number;
}

const BRACKET_COLORS = [
    "#fff",     // 1: White
    "#1a1a1a",  // 2: Black
    "#ef4444",  // 3: Red
    "#3b82f6",  // 4: Blue
    "#eab308",  // 5: Yellow
    "#16a34a",  // 6: Green
    "#ea580c",  // 7: Orange
    "#f472b6",  // 8: Pink
] as const;

// Brackets that need black text
const LIGHT_BRACKETS = new Set([1, 5]);

export const LiveRanking = ({ entries, progress, totalDistance }: LiveRankingProps) => {
    // Create an array of indices [0, 1, ..., n]
    const indices = entries.map((_, i) => i);

    // Sort indices based on progress (descending)
    const sortedIndices = indices.sort((a, b) => {
        return (progress[b] ?? 0) - (progress[a] ?? 0);
    });

    const topLeader = progress[sortedIndices[0]] ?? 0;

    return (
        <div className="sim-ranking">
            <div className="sim-ranking__header">
                <span>🏆 Live Ranking</span>
                <span style={{ fontSize: "var(--text-xs)", fontWeight: "normal", color: "var(--color-text-sub)" }}>
                    {totalDistance}m
                </span>
            </div>

            <div className="sim-ranking__list">
                {sortedIndices.map((originalIndex, rankIndex) => {
                    const entry = entries[originalIndex];
                    const dist = progress[originalIndex] ?? 0;
                    const isFinished = dist >= totalDistance;

                    const bracket = entry.bracket_number ?? 1;
                    // Use index 0-7 for color, fallback to grey
                    const colorIndex = Math.max(0, Math.min(bracket - 1, 7));
                    const badgeBg = BRACKET_COLORS[colorIndex];
                    const badgeColor = LIGHT_BRACKETS.has(bracket) ? "#000" : "#fff";

                    // Calculate gap from leader (meters)
                    const gap = topLeader - dist;

                    return (
                        <div key={entry.horse_number} className="sim-ranking__item">
                            <div className={`sim-ranking__rank rank-${rankIndex + 1}`}>
                                {rankIndex + 1}
                            </div>

                            <div
                                className="sim-result-badge"
                                style={{ backgroundColor: badgeBg, color: badgeColor, minWidth: 24 }}
                            >
                                {entry.horse_number}
                            </div>

                            <div className="sim-ranking__horse-info">
                                <div className="sim-ranking__horse-name">
                                    {entry.horse.name}
                                </div>
                                <div className="sim-ranking__jockey">
                                    {entry.jockey}
                                </div>
                            </div>

                            <div className="sim-ranking__gap">
                                {isFinished ? (
                                    <span className="text-success">GOAL</span>
                                ) : rankIndex === 0 ? (
                                    <span className="text-primary">{Math.round(dist)}m</span>
                                ) : (
                                    <span className="text-muted">-{gap.toFixed(1)}m</span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
