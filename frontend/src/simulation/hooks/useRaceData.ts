/**
 * レースデータ取得を管理するカスタムフック
 *
 * レース一覧・レース詳細・馬分析データをまとめて管理する。
 */
import { useEffect, useState, useCallback } from "react";
import { raceApi } from "../../api/raceApi";
import type {
    HorseAnalysisResponse,
    RaceDetailResponse,
    RaceListItem,
} from "../../types";

interface UseRaceDataReturn {
    /** レース一覧 */
    races: RaceListItem[];
    /** 選択中のレースID */
    selectedRaceId: string;
    /** レースIDを選択 */
    selectRace: (raceId: string) => void;
    /** 選択中レースの詳細 */
    raceDetail: RaceDetailResponse | null;
    /** 馬ごとの分析データ (horse_id → HorseAnalysisResponse) */
    horseAnalyses: Record<string, HorseAnalysisResponse>;
    /** データ読み込み中か */
    loading: boolean;
}

export function useRaceData(): UseRaceDataReturn {
    const [races, setRaces] = useState<RaceListItem[]>([]);
    const [selectedRaceId, setSelectedRaceId] = useState("");
    const [raceDetail, setRaceDetail] = useState<RaceDetailResponse | null>(null);
    const [horseAnalyses, setHorseAnalyses] = useState<
        Record<string, HorseAnalysisResponse>
    >({});
    const [loading, setLoading] = useState(false);

    // レース一覧取得
    useEffect(() => {
        const fetchRaces = async () => {
            try {
                const data = await raceApi.getRaces();
                setRaces(data);
                if (data.length > 0) {
                    setSelectedRaceId(data[0].race_id);
                }
            } catch (e: unknown) {
                // eslint-disable-next-line no-console
                console.error("Failed to fetch races:", e);
            }
        };
        void fetchRaces();
    }, []);

    // レース詳細 & 馬分析データの読み込み
    const loadRaceData = useCallback(async (raceId: string) => {
        setLoading(true);
        try {
            const detail = await raceApi.getRaceDetail(raceId);
            setRaceDetail(detail);

            // 一括取得APIを使用
            const analyses = await raceApi.getRaceAnalysis(raceId);
            setHorseAnalyses(analyses);
        } catch (e: unknown) {
            // eslint-disable-next-line no-console
            console.error("Failed to load race data:", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (selectedRaceId) {
            void loadRaceData(selectedRaceId);
        }
    }, [selectedRaceId, loadRaceData]);

    const selectRace = useCallback((raceId: string) => {
        setSelectedRaceId(raceId);
    }, []);

    return {
        races,
        selectedRaceId,
        selectRace,
        raceDetail,
        horseAnalyses,
        loading,
    };
}
