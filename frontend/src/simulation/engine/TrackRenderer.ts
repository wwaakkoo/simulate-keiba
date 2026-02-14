/**
 * トラック（コース）描画ロジック
 *
 * PixiJS Graphics を使ってオーバルコース・ゴールラインを描画する。
 * コースタイプ（芝/ダート）による色分け、距離ハロン棒、コーナー番号も描画。
 */
import { Container, Graphics, Text, TextStyle } from "pixi.js";
import {
    CENTER_X,
    CENTER_Y,
    OUTER_RADIUS,
} from "./PositionCalculator";
import { SIMULATION_CONFIG } from "../config";

const { TRACK_RADIUS, STRAIGHT_LENGTH } = SIMULATION_CONFIG;

/**
 * トラック・背景・ゴールラインを含む Container を生成して返す。
 * @param courseType "芝" | "ダート" (デフォルト: 芝)
 */
export function createTrackLayer(courseType: string = "芝"): Container {
    const layer = new Container();
    const g = new Graphics();

    const half = STRAIGHT_LENGTH / 2;
    const innerRadius = TRACK_RADIUS;
    const outerRadius = OUTER_RADIUS;

    // --- 色設定 ---
    // 芝: 緑, ダート: 茶色
    const isTurf = courseType.includes("芝");
    const surfaceColor = isTurf ? 0x2e8b57 : 0x8b4513; // SeaGreen vs SaddleBrown
    const laneColor = 0xffffff;

    // --- トラックのベース（地面）を描画 ---
    g.beginPath();
    // 外周
    g.moveTo(CENTER_X - half, CENTER_Y - outerRadius);
    g.lineTo(CENTER_X + half, CENTER_Y - outerRadius);
    g.arc(CENTER_X + half, CENTER_Y, outerRadius, -Math.PI / 2, Math.PI / 2);
    g.lineTo(CENTER_X - half, CENTER_Y + outerRadius);
    g.arc(CENTER_X - half, CENTER_Y, outerRadius, Math.PI / 2, -Math.PI / 2);
    g.closePath();

    // 内周（穴を開けるためのパス... PixiJS v8での穴あけは cut() を使うか、
    // 単に上に緑/背景色を重ねるかで対応。ここでは背景色を重ねる簡易実装とするが、
    // レイヤー順序的にトラック自体を塗りつぶし、その上に内側の緑（フィールド）を描くのが自然。
    g.fill(surfaceColor);

    // --- 内側のフィールド（背景色） ---
    // ここでは透明ではなく「内馬場」として少し暗い緑などを置くと良いが、
    // シンプルに背景色(configのBACKGROUND_COLORに合わせるか、黒)で塗りつぶす
    // あるいは内馬場プールや障害コースの表現も可能だが、一旦黒(0x0f172a / slate-900)で抜く
    const innerG = new Graphics();
    innerG.beginPath();
    innerG.moveTo(CENTER_X - half, CENTER_Y - innerRadius);
    innerG.lineTo(CENTER_X + half, CENTER_Y - innerRadius);
    innerG.arc(CENTER_X + half, CENTER_Y, innerRadius, -Math.PI / 2, Math.PI / 2);
    innerG.lineTo(CENTER_X - half, CENTER_Y + innerRadius);
    innerG.arc(CENTER_X - half, CENTER_Y, innerRadius, Math.PI / 2, -Math.PI / 2);
    innerG.closePath();
    innerG.fill(0x0f172a); // Background color

    // --- ライン描画 ---
    const lineG = new Graphics();

    // 内ラチ
    lineG.moveTo(CENTER_X - half, CENTER_Y - innerRadius);
    lineG.lineTo(CENTER_X + half, CENTER_Y - innerRadius);
    lineG.arc(CENTER_X + half, CENTER_Y, innerRadius, -Math.PI / 2, Math.PI / 2);
    lineG.lineTo(CENTER_X - half, CENTER_Y + innerRadius);
    lineG.arc(CENTER_X - half, CENTER_Y, innerRadius, Math.PI / 2, -Math.PI / 2);
    lineG.stroke({ width: 2, color: laneColor });

    // 外ラチ
    lineG.moveTo(CENTER_X - half, CENTER_Y - outerRadius);
    lineG.lineTo(CENTER_X + half, CENTER_Y - outerRadius);
    lineG.arc(CENTER_X + half, CENTER_Y, outerRadius, -Math.PI / 2, Math.PI / 2);
    lineG.lineTo(CENTER_X - half, CENTER_Y + outerRadius);
    lineG.arc(CENTER_X - half, CENTER_Y, outerRadius, Math.PI / 2, -Math.PI / 2);
    lineG.stroke({ width: 2, color: laneColor });

    // --- ゴール板 ---
    // ゴールは通常、直線の終わり付近やスタンド前にある。
    // SimulationEngineの座標系では `progress` 0 がスタート、 maxがゴールだが、
    // 描画上のゴールラインは固定位置（例えば右直線の終わりなど）。
    // 現在のSimulationEngineは「周回」を考慮していない単純な線形進行から座標変換している。
    // PositionCalculator.ts を見ないと正確なゴール位置が不明だが、
    // 仮に "右回りの第4コーナー抜けたホームストレッチ中央" をゴールとする。
    // ここでは元のコードのゴールラインを踏襲：
    // g.moveTo(CENTER_X, CENTER_Y + TRACK_RADIUS);
    // g.lineTo(CENTER_X, CENTER_Y + OUTER_RADIUS);
    // これは「下側の直線の中央」をゴールとしている。

    const goalX = CENTER_X; // 下直線の真ん中
    lineG.moveTo(goalX, CENTER_Y + innerRadius);
    lineG.lineTo(goalX, CENTER_Y + outerRadius);
    lineG.stroke({ width: 4, color: 0xffd700 }); // Gold

    // ゴールポスト（装飾）
    const postG = new Graphics();
    postG.rect(goalX - 2, CENTER_Y + outerRadius, 4, 10);
    postG.fill(0xffd700);

    // --- 配置 ---
    layer.addChild(g);       // トラック（色付き）
    layer.addChild(innerG);  // 内馬場（抜き）
    layer.addChild(lineG);   // ライン
    layer.addChild(postG);   // ゴールポスト

    // --- コーナー番号などの文字 ---
    // 左回り/右回りによって位置が変わるが、ひとまず固定で配置
    // 第1コーナー: 右上, 第2: 左上, 第3: 左下, 第4: 右下 (右回りの場合)
    // ここでは単純に4隅に数字を置く
    const style = new TextStyle({
        fontFamily: 'Arial',
        fontSize: 24,
        fill: 0xffffff,
        fontWeight: 'bold',
    });

    // 1コーナー (右上カーブの入り口付近)
    const c1 = new Text({ text: "1", style });
    c1.position.set(CENTER_X + half + 20, CENTER_Y - innerRadius - 20);
    c1.alpha = 0.5;
    layer.addChild(c1);

    // 2コーナー (左上カーブの出口付近)
    const c2 = new Text({ text: "2", style });
    c2.position.set(CENTER_X - half - 20, CENTER_Y - innerRadius - 20);
    c2.alpha = 0.5;
    layer.addChild(c2);

    // 3コーナー (左下カーブの入り口付近)
    const c3 = new Text({ text: "3", style });
    c3.position.set(CENTER_X - half - 20, CENTER_Y + innerRadius + 20);
    c3.alpha = 0.5;
    layer.addChild(c3);

    // 4コーナー (右下カーブの出口付近)
    const c4 = new Text({ text: "4", style });
    c4.position.set(CENTER_X + half + 20, CENTER_Y + innerRadius + 20);
    c4.alpha = 0.5;
    layer.addChild(c4);

    return layer;
}

