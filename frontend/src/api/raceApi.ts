import type { HorseAnalysisResponse, RaceDetailResponse, RaceListItem } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

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

    // レース出走馬の全分析データ取得 (一括)
    getRaceAnalysis: async (raceId: string): Promise<Record<string, HorseAnalysisResponse>> => {
        const response = await fetch(`${API_BASE}/races/${raceId}/analysis`);
        if (!response.ok) throw new Error("Failed to fetch race analysis");
        return response.json();
    },

    // 馬の分析データ取得 (個別)
    getHorseAnalysis: async (horseId: string): Promise<HorseAnalysisResponse> => {
        const response = await fetch(`${API_BASE}/analysis/horses/${horseId}`);
        if (!response.ok) throw new Error("Failed to fetch horse analysis");
        return response.json();
    },
};
