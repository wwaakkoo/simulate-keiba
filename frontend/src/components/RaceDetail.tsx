import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { raceApi } from "../api/raceApi";
import { apiClient } from "../api/client";
import type { RaceDetailResponse, HorseAnalysisResponse, PredictionResponse } from "../types";

export const RaceDetail = () => {
    const { raceId } = useParams<{ raceId: string }>();
    const [race, setRace] = useState<RaceDetailResponse | null>(null);
    const [analysis, setAnalysis] = useState<Record<string, HorseAnalysisResponse>>({});
    const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [isPredicting, setIsPredicting] = useState(false);
    const [error, setError] = useState("");

    const handlePredict = async () => {
        if (!raceId) return;
        setIsPredicting(true);
        try {
            const result = await apiClient.predictRace(raceId);
            setPrediction(result);
        } catch (err) {
            console.error("Prediction failed:", err);
            alert("Prediction failed. Please try again.");
        } finally {
            setIsPredicting(false);
        }
    };

    useEffect(() => {
        if (!raceId) return;

        const loadData = async () => {
            try {
                const raceData = await raceApi.getRaceDetail(raceId);
                setRace(raceData);

                // Try to fetch analysis/predictions, but don't block if stats are missing
                try {
                    const analysisData = await raceApi.getRaceAnalysis(raceId);
                    setAnalysis(analysisData);
                } catch (e) {
                    console.warn("Analysis data not available", e);
                }
            } catch (err) {
                console.error(err);
                setError("Failed to load race data.");
            } finally {
                setLoading(false);
            }
        };
        void loadData();
    }, [raceId]);

    if (loading) return <div className="p-8 text-center text-muted">Loading race details...</div>;
    if (error || !race) return <div className="p-8 text-center text-danger">{error || "Race not found"}</div>;

    const predictionMap = prediction ? Object.fromEntries(
        prediction.predictions.map(p => [p.horse_number, p])
    ) : {};

    return (
        <div className="app-container p-4 max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono bg-surface-hover px-2 py-1 rounded text-muted">
                            {race.date}
                        </span>
                        <span className="text-xs font-mono bg-surface-hover px-2 py-1 rounded text-muted">
                            {race.venue}
                        </span>
                    </div>
                    <h1 className="text-3xl font-bold mb-2">{race.name}</h1>
                    <div className="flex gap-4 text-sm text-sub">
                        <span>{race.course_type} {race.distance}m</span>
                        <span>{race.weather || "Weather: Unknown"}</span>
                        <span>{race.track_condition || "Condition: Unknown"}</span>
                        <span>{race.entries.length} Entries</span>
                    </div>
                </div>

                <div className="flex gap-3">
                    <Link to="/races" className="btn btn-ghost">Back to List</Link>

                    <button
                        onClick={handlePredict}
                        disabled={isPredicting}
                        className="btn btn-secondary px-6 flex items-center gap-2"
                    >
                        {isPredicting ? "Predicting..." : "Predict AI 🤖"}
                    </button>

                    <Link to={`/simulation?raceId=${race.race_id}`} className="btn btn-primary px-6">
                        Start Simulation
                    </Link>
                </div>
            </div>

            {/* Entry Table */}
            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead className="bg-surface-hover">
                        <tr>
                            <th className="p-3 text-center text-sm text-muted font-normal w-12">No</th>
                            <th className="p-3 text-left text-sm text-muted font-normal">Horse</th>
                            <th className="p-3 text-left text-sm text-muted font-normal">Jockey</th>
                            <th className="p-3 text-right text-sm text-muted font-normal">Odds</th>
                            <th className="p-3 text-right text-sm text-muted font-normal">Prediction (Style)</th>
                            {prediction && <th className="p-3 text-center text-sm text-muted font-normal">AI Rank</th>}
                            <th className="p-3 text-right text-sm text-muted font-normal">Result</th>
                        </tr>
                    </thead>
                    <tbody>
                        {race.entries.map((entry) => {
                            const horseAnalysis = analysis[entry.horse.horse_id];
                            const pred = predictionMap[entry.horse_number];

                            return (
                                <tr key={entry.horse_number} style={{ borderTop: "1px solid var(--color-border)" }} className="hover:bg-surface-hover transition-colors">
                                    <td className="p-3 text-center text-main font-bold">{entry.horse_number}</td>
                                    <td className="p-3">
                                        <div className="font-bold text-main">{entry.horse.name}</div>
                                        {horseAnalysis && (
                                            <div className="text-xs text-muted flex gap-2 mt-1">
                                                <span>Speed: {horseAnalysis.stats?.speed_rating || "-"}</span>
                                                <span>Stamina: {horseAnalysis.stats?.stamina_rating || "-"}</span>
                                            </div>
                                        )}
                                    </td>
                                    <td className="p-3 text-sm text-sub">
                                        {entry.jockey}
                                        <div className="text-xs text-muted">{entry.weight_carried}kg</div>
                                    </td>
                                    <td className="p-3 text-right font-mono text-main">
                                        {entry.odds?.toFixed(1) ?? "-"}
                                    </td>
                                    <td className="p-3 text-right text-sm">
                                        {horseAnalysis ? (
                                            <span className="px-2 py-1 rounded bg-surface-active text-xs">
                                                {horseAnalysis.style}
                                            </span>
                                        ) : (
                                            <span className="text-muted text-xs">-</span>
                                        )}
                                    </td>

                                    {prediction && (
                                        <td className="p-3 text-center">
                                            {pred ? (
                                                <div className="flex flex-col items-center">
                                                    <span className={`font-bold text-lg ${pred.predicted_rank <= 3 ? "text-warning" : "text-sub"}`}>
                                                        {pred.mark} {pred.predicted_rank}
                                                    </span>
                                                    <span className="text-[10px] text-muted">
                                                        ({pred.predicted_position.toFixed(2)})
                                                    </span>
                                                </div>
                                            ) : "-"}
                                        </td>
                                    )}

                                    <td className="p-3 text-right">
                                        {entry.finish_position ? (
                                            <span className={`text-sm font-bold ${entry.finish_position === 1 ? "text-warning" :
                                                entry.finish_position <= 3 ? "text-primary-light" : "text-muted"
                                                }`}>
                                                {entry.finish_position}
                                            </span>
                                        ) : (
                                            <span className="text-muted">-</span>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
