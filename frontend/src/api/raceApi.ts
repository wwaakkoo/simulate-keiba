import type { HorseAnalysisResponse, RaceDetailResponse, RaceListItem } from "../types";

const API_BASE = "http://localhost:8000/api";

export const raceApi = {
    // レース一覧取得
    getRaces: async (): Promise<RaceListItem[]> => {
        const response = await fetch(`${API_BASE}/races`);
        if (!response.ok) throw new Error("Failed to fetch races");
        return response.json();
    },

    // レース詳細取得
    getRaceDetail: async (raceId: string): Promise<RaceDetailResponse> => {
        const response = await fetch(`${API_BASE}/races/${raceId}`);
        if (!response.ok) throw new Error("Failed to fetch race detail");
        return response.json();
    },

    // 馬の分析データ取得
    getHorseAnalysis: async (horseId: string): Promise<HorseAnalysisResponse> => {
        const response = await fetch(`${API_BASE}/analysis/horses/${horseId}`);
        if (!response.ok) throw new Error("Failed to fetch horse analysis");
        return response.json();
    },
};
