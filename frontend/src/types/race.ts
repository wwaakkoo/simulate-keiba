/**
 * レースに関する型定義
 */

/** 馬の情報 */
export interface Horse {
    id: string;
    name: string;
    number: number;
    jockey: string;
    trainer: string;
    weight: number;
    age: number;
    sex: string;
}

/** レース情報 */
export interface Race {
    id: string;
    name: string;
    date: string;
    venue: string;
    course: string;
    distance: number;
    surfaceType: 'turf' | 'dirt';
    entries: Horse[];
}

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
