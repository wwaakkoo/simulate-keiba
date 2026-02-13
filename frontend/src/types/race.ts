/**
 * ドメイン型定義
 *
 * 将来の予測エンジンUI・結果分析で使用するドメインモデル型。
 * ※ APIレスポンス型は types/index.ts を参照。
 */

/** 予測結果 */
export interface Prediction {
    raceId: string;
    predictions: HorsePrediction[];
    modelVersion: string;
    createdAt: string;
}

/** 個別馬の予測 */
export interface HorsePrediction {
    horseId: string;
    horseName: string;
    predictedRank: number;
    winProbability: number;
    expectedSpeed: number;
}

/** 実際のレース結果 */
export interface RaceResult {
    raceId: string;
    results: HorseResult[];
}

/** 個別馬の結果 */
export interface HorseResult {
    horseId: string;
    horseName: string;
    finishPosition: number;
    finishTime: string;
    margin: string;
}
