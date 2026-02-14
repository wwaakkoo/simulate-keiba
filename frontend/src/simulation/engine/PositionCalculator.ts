/**
 * コース上の進行距離から (x, y) 座標を計算するユーティリティ
 *
 * トラックは「上下の直線 + 左右の半円カーブ」で構成される楕円コース。
 *
 * 単位系:
 *   - すべてのパブリック API は「メートル」を受け取る
 *   - 内部でピクセルに変換して描画座標を返す
 *   - 1周 = METERS_PER_LAP メートル（中山競馬場相当）
 */
import { SIMULATION_CONFIG } from "../config";

const {
    WIDTH: COURSE_WIDTH,
    HEIGHT: COURSE_HEIGHT,
    TRACK_RADIUS,
    STRAIGHT_LENGTH,
} = SIMULATION_CONFIG;

// ─── 定数 ─────────────────────────────────────────

/** コースの中心座標 (px) */
export const CENTER_X = COURSE_WIDTH / 2;
export const CENTER_Y = COURSE_HEIGHT / 2;

/** コース外周の全長 (px) */
export const TRACK_PERIMETER_PX =
    2 * STRAIGHT_LENGTH + 2 * Math.PI * TRACK_RADIUS;

/** 1周の長さ (メートル) — 中山競馬場の内回り相当 */
export const METERS_PER_LAP = 1700;

/** メートル → ピクセルの変換係数 */
export const METERS_TO_PX = TRACK_PERIMETER_PX / METERS_PER_LAP;

/** 外側レーンのオフセット幅 (px) */
const OUTER_OFFSET = 80;

/** 外側トラック半径 (px) */
export const OUTER_RADIUS = TRACK_RADIUS + OUTER_OFFSET;

// ─── 座標計算 ─────────────────────────────────────

/**
 * メートル単位の進行距離からコース上の描画座標を返す。
 *
 * ゴール = d=0 の位置 (下側直線の中央)。
 * d > METERS_PER_LAP の場合は自動的に周回処理される。
 *
 * @param meters      - 進行距離 (メートル)
 * @param laneOffset  - 内外のオフセット (px)
 */
export function getTrackPosition(
    meters: number,
    laneOffset: number,
): { x: number; y: number } {
    // メートル → ピクセルに変換し、1周分に正規化
    const px =
        ((meters * METERS_TO_PX) % TRACK_PERIMETER_PX + TRACK_PERIMETER_PX) %
        TRACK_PERIMETER_PX;

    return getTrackPositionPx(px, laneOffset);
}

/**
 * ピクセル単位でのコース座標計算 (内部用)
 *
 * コースを5セグメントに分割:
 *   1. 下側直線・左半分 (ゴール → 左端)
 *   2. 左カーブ (下→上)
 *   3. 上側直線 (左→右)
 *   4. 右カーブ (上→下)
 *   5. 下側直線・右半分 (右端 → ゴール)
 */
function getTrackPositionPx(
    d: number,
    laneOffset: number,
): { x: number; y: number } {
    const half = STRAIGHT_LENGTH / 2;
    const curveLength = Math.PI * TRACK_RADIUS;

    // セグメント1: 下側直線・左半分（ゴール → 左端）
    const seg1End = half;
    if (d < seg1End) {
        return {
            x: CENTER_X - d,
            y: CENTER_Y + TRACK_RADIUS + laneOffset,
        };
    }

    // セグメント2: 左カーブ（下→上）
    const seg2End = seg1End + curveLength;
    if (d < seg2End) {
        const theta = Math.PI / 2 + (d - seg1End) / TRACK_RADIUS;
        return {
            x: CENTER_X - half + Math.cos(theta) * (TRACK_RADIUS + laneOffset),
            y: CENTER_Y + Math.sin(theta) * (TRACK_RADIUS + laneOffset),
        };
    }

    // セグメント3: 上側直線（左→右）
    const seg3End = seg2End + STRAIGHT_LENGTH;
    if (d < seg3End) {
        const d2 = d - seg2End;
        return {
            x: CENTER_X - half + d2,
            y: CENTER_Y - TRACK_RADIUS - laneOffset,
        };
    }

    // セグメント4: 右カーブ（上→下）
    const seg4End = seg3End + curveLength;
    if (d < seg4End) {
        const theta = -Math.PI / 2 + (d - seg3End) / TRACK_RADIUS;
        return {
            x: CENTER_X + half + Math.cos(theta) * (TRACK_RADIUS + laneOffset),
            y: CENTER_Y + Math.sin(theta) * (TRACK_RADIUS + laneOffset),
        };
    }

    // セグメント5: 下側直線・右半分（右端 → ゴール）
    const d5 = d - seg4End;
    return {
        x: CENTER_X + half - d5,
        y: CENTER_Y + TRACK_RADIUS + laneOffset,
    };
}

/**
 * レース距離からスタート位置のオフセット (メートル) を算出する。
 *
 * ゴール = d=0。スタートはゴールから raceDistance メートル手前。
 * 2500m のレースなら: ゴールから 2500m 逆方向 = 1周半弱手前からスタート。
 *
 * 返す値はコース上の正の位置 (メートル)。
 */
export function calculateStartOffset(raceDistance: number): number {
    return (
        (METERS_PER_LAP - (raceDistance % METERS_PER_LAP)) % METERS_PER_LAP
    );
}

/**
 * 進行距離(メートル)に対応するトラック上の向き(ラジアン)を返す。
 * 0 = 右向き, PI/2 = 下向き, PI = 左向き, -PI/2 = 上向き
 */
export function getTrackRotation(meters: number): number {
    // メートル → ピクセルに変換し、1周分に正規化
    const px =
        ((meters * METERS_TO_PX) % TRACK_PERIMETER_PX + TRACK_PERIMETER_PX) %
        TRACK_PERIMETER_PX;

    const half = STRAIGHT_LENGTH / 2;
    const curveLength = Math.PI * TRACK_RADIUS;

    // セグメント1: 下側直線・左半分（ゴール → 左端） -> 左向き
    const seg1End = half;
    if (px < seg1End) {
        return Math.PI;
    }

    // セグメント2: 左カーブ（下→上）
    const seg2End = seg1End + curveLength;
    if (px < seg2End) {
        // theta は PI/2 (下) から PI*1.5 (上) へ
        // 進行方向は接線なので theta + PI/2
        const theta = Math.PI / 2 + (px - seg1End) / TRACK_RADIUS;
        return theta + Math.PI / 2;
    }

    // セグメント3: 上側直線（左→右） -> 右向き
    const seg3End = seg2End + STRAIGHT_LENGTH;
    if (px < seg3End) {
        return 0;
    }

    // セグメント4: 右カーブ（上→下）
    const seg4End = seg3End + curveLength;
    if (px < seg4End) {
        // theta は -PI/2 (上) から PI/2 (下) へ
        const theta = -Math.PI / 2 + (px - seg3End) / TRACK_RADIUS;
        return theta + Math.PI / 2;
    }

    // セグメント5: 下側直線・右半分（右端 → ゴール） -> 左向き
    return Math.PI;
}
