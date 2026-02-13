/**
 * APIレスポンス型定義
 *
 * バックエンド (FastAPI Pydantic schemas) と 1:1 で対応する型。
 * ドメイン型（予測・結果分析用）は types/race.ts を参照。
 */

export interface HorseResponse {
    horse_id: string;
    name: string;
    sex?: string;
    trainer?: string;
    sire?: string;
    dam?: string;
}

export interface EntryResponse {
    horse_number: number;
    bracket_number?: number;
    horse: HorseResponse;
    jockey?: string;
    weight_carried?: number;
    odds?: number;
    popularity?: number;
    finish_position?: number;
    finish_time?: string;
    margin?: string;
    passing_order?: string;
    last_3f?: number;
    horse_weight?: number;
    horse_weight_diff?: number;
    status: string;
}

export interface RaceListItem {
    race_id: string;
    name: string;
    date: string;
    venue: string;
    course_type: string;
    distance: number;
    track_condition?: string;
    race_class?: string;
    num_entries?: number;
}

export interface RaceDetailResponse {
    race_id: string;
    name: string;
    date: string;
    venue: string;
    course_type: string;
    distance: number;
    direction?: string;
    weather?: string;
    track_condition?: string;
    race_class?: string;
    num_entries?: number;
    entries: EntryResponse[];
}

export interface HorseAnalysisResponse {
    horse_id: string;
    name: string;
    style: string;
    stats: Record<string, number>;
}
