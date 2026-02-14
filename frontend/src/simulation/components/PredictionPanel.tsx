import React from "react";
import type { PredictionResponse } from "../../types/prediction";

import "./PredictionPanel.css";

interface Props {
    data: PredictionResponse | null;
    isLoading: boolean;
    error: Error | null;
    onPredict: () => void;
}

export const PredictionPanel: React.FC<Props> = ({
    data,
    isLoading,
    error,
    onPredict,
}) => {
    return (
        <div className="prediction-panel">
            <div className="panel-header">
                <h3>AI着順予測 (Beta)</h3>
                <button
                    className="predict-button"
                    onClick={onPredict}
                    disabled={isLoading}
                >
                    {isLoading ? "予測中..." : "AI予測を実行"}
                </button>
            </div>

            {error && <div className="error-message">予測エラー: {error.message}</div>}

            {data && (
                <div className="prediction-results">
                    <div className="model-info">
                        Based on: {data.method} ({data.model_version})
                    </div>
                    <table className="prediction-table">
                        <thead>
                            <tr>
                                <th>印</th>
                                <th>予順</th>
                                <th>馬番</th>
                                <th>馬名</th>
                                <th>スコア</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.predictions.map((p) => (
                                <tr key={p.horse_number} className={`rank-${p.predicted_rank}`}>
                                    <td className="mark-cell">{p.mark}</td>
                                    <td>{p.predicted_rank}</td>
                                    <td>{p.horse_number}</td>
                                    <td className="horse-name">{p.horse_name}</td>
                                    <td>{p.predicted_position.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};
