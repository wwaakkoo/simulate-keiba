export interface PredictionItem {
    horse_name: string;
    horse_number: number;
    predicted_position: number;
    predicted_rank: number;
    mark: string;
}

export interface PredictionResponse {
    race_id: string;
    predictions: PredictionItem[];
    model_version: string;
    method: string;
}
