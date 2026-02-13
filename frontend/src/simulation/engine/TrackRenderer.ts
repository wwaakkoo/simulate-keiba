/**
 * トラック（コース）描画ロジック
 *
 * PixiJS Graphics を使ってオーバルコース・ゴールラインを描画する。
 */
import { Container, Graphics } from "pixi.js";
import {
    CENTER_X,
    CENTER_Y,
    OUTER_RADIUS,
} from "./PositionCalculator";
import { SIMULATION_CONFIG } from "../config";

const { TRACK_RADIUS, STRAIGHT_LENGTH } = SIMULATION_CONFIG;

/**
 * トラック・背景・ゴールラインを含む Container を生成して返す。
 */
export function createTrackLayer(): Container {
    const layer = new Container();
    const g = new Graphics();
    const half = STRAIGHT_LENGTH / 2;

    // --- 内側のトラックライン ---
    g.moveTo(CENTER_X - half, CENTER_Y - TRACK_RADIUS);
    g.lineTo(CENTER_X + half, CENTER_Y - TRACK_RADIUS);
    g.arc(CENTER_X + half, CENTER_Y, TRACK_RADIUS, -Math.PI / 2, Math.PI / 2);
    g.lineTo(CENTER_X - half, CENTER_Y + TRACK_RADIUS);
    g.arc(CENTER_X - half, CENTER_Y, TRACK_RADIUS, Math.PI / 2, -Math.PI / 2);
    g.stroke({ width: 4, color: 0xffffff });

    // --- 外側のトラックライン ---
    g.moveTo(CENTER_X - half, CENTER_Y - OUTER_RADIUS);
    g.lineTo(CENTER_X + half, CENTER_Y - OUTER_RADIUS);
    g.arc(CENTER_X + half, CENTER_Y, OUTER_RADIUS, -Math.PI / 2, Math.PI / 2);
    g.lineTo(CENTER_X - half, CENTER_Y + OUTER_RADIUS);
    g.arc(CENTER_X - half, CENTER_Y, OUTER_RADIUS, Math.PI / 2, -Math.PI / 2);
    g.stroke({ width: 2, color: 0xffffff });

    // --- ゴールライン ---
    g.moveTo(CENTER_X, CENTER_Y + TRACK_RADIUS);
    g.lineTo(CENTER_X, CENTER_Y + OUTER_RADIUS);
    g.stroke({ width: 4, color: 0xffff00 });

    layer.addChild(g);
    return layer;
}
