
import type { EntryResponse, HorseAnalysisResponse } from "../../types";

/** 1頭ごとのシミュレーション結果 */
export interface SimResult {
    horseNumber: number;
    time: number;
}

/** エンジン初期化時に渡す馬データ */
export interface HorseSetup {
    index: number;
    horseNumber: number;
    entry: EntryResponse;
    analysis: HorseAnalysisResponse | undefined;
}

/** コールバック型 */
export type OnHorseFinish = (result: SimResult) => void;
export type OnAllFinish = () => void;
