/**
 * 出走馬詳細テーブル
 */
import type { EntryResponse, HorseAnalysisResponse } from "../../types";

interface EntryTableProps {
    entries: EntryResponse[];
    horseAnalyses: Record<string, HorseAnalysisResponse>;
}

/** 脚質ラベルの日本語マッピング */
const STYLE_LABEL: Record<string, string> = {
    NIGE: "逃げ",
    SENKO: "先行",
    SASHI: "差し",
    OIKOMI: "追込",
    UNKNOWN: "不明",
};

/** ステータスの日本語マッピング */
function statusLabel(status: string): string {
    switch (status) {
        case "scratched":
            return "取消";
        case "excluded":
            return "除外";
        case "dnf":
            return "中止";
        default:
            return "";
    }
}

export const EntryTable = ({ entries, horseAnalyses }: EntryTableProps) => (
    <div className="sim-entry-table">
        <h3 className="sim-entry-table__title">🏇 出走馬詳細情報</h3>
        <table className="sim-entry-table__table">
            <thead>
                <tr>
                    <th>枠-番</th>
                    <th>馬名</th>
                    <th>騎手 / 斤量</th>
                    <th>脚質予測</th>
                    <th>単勝オッズ</th>
                    <th>実際の結果</th>
                </tr>
            </thead>
            <tbody>
                {entries.map((entry) => {
                    const analysis = horseAnalyses[entry.horse.horse_id];
                    return (
                        <tr key={entry.horse_number}>
                            <td className="sim-entry-table__bracket">
                                <span className="sim-entry-table__bracket-sub">
                                    {entry.bracket_number}-
                                </span>
                                <strong className="sim-entry-table__bracket-main">
                                    {entry.horse_number}
                                </strong>
                            </td>
                            <td className="sim-entry-table__name">
                                <div className="sim-entry-table__horse-name">
                                    {entry.horse.name}
                                </div>
                                <div className="sim-entry-table__horse-meta">
                                    {entry.horse.sex} / {entry.horse.trainer}
                                </div>
                            </td>
                            <td className="sim-entry-table__jockey">
                                {entry.jockey} / {entry.weight_carried}kg
                            </td>
                            <td className="sim-entry-table__style">
                                <span className="sim-entry-table__style-badge">
                                    {analysis
                                        ? (STYLE_LABEL[analysis.style] ?? analysis.style)
                                        : "分析中..."}
                                </span>
                            </td>
                            <td className="sim-entry-table__odds">
                                <div
                                    className={`sim-entry-table__odds-value ${(entry.popularity ?? 99) <= 3 ? "sim-entry-table__odds-value--hot" : ""}`}
                                >
                                    {entry.odds?.toFixed(1) ?? "-"}
                                </div>
                                <div className="sim-entry-table__popularity">
                                    {entry.popularity}番人気
                                </div>
                            </td>
                            <td className="sim-entry-table__result">
                                {entry.status === "result" ? (
                                    entry.finish_position ? (
                                        <div className="sim-entry-table__result-detail">
                                            <span className="sim-entry-table__result-position">
                                                {entry.finish_position}着
                                            </span>
                                            <span className="sim-entry-table__result-time">
                                                {entry.finish_time}
                                            </span>
                                        </div>
                                    ) : (
                                        "未確定"
                                    )
                                ) : (
                                    <span className="sim-entry-table__result-status">
                                        {statusLabel(entry.status)}
                                    </span>
                                )}
                            </td>
                        </tr>
                    );
                })}
            </tbody>
        </table>
    </div>
);
