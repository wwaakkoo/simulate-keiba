import { Container, Graphics, Text, TextStyle } from 'pixi.js';
import { SIMULATION_CONFIG } from "../config";

const HORSE_RADIUS = 15;
const COLORS = SIMULATION_CONFIG.COLORS;

export class HorseSprite extends Container {
    private _horseNumber: number;
    private _color: number;
    private _graphics: Graphics;
    private _text: Text;

    public get horseNumber(): number {
        return this._horseNumber;
    }

    constructor(horseNumber: number, bracketNumber: number) {
        super();
        this._horseNumber = horseNumber;
        this._color = COLORS[bracketNumber] || 0xcccccc;

        this._graphics = new Graphics();
        this.addChild(this._graphics);
        this.drawHorse();

        // 馬番テキスト
        const style = new TextStyle({
            fontFamily: 'Arial',
            fontSize: 14,
            fill: bracketNumber === 2 ? '#ffffff' : '#000000', // 黒枠のときは白文字
            fontWeight: 'bold',
        });
        this._text = new Text({ text: String(horseNumber), style });
        this._text.anchor.set(0.5);
        this.addChild(this._text);
    }

    private drawHorse() {
        this._graphics.clear();

        // 馬体（細長い楕円） - 進行方向に向かって描画
        // 左向き(デフォルト)で描いて、rotationで回す想定
        // しかしPixiのrotation 0は「右」が基準のことが多いが、
        // getTrackRotationは 直線(右向き) = 0 を返すと仮定。
        // ここでは (0,0) を中心に、右を向いた馬を描く。

        // 体 (茶色)
        this._graphics.ellipse(0, 0, 18, 8); // 横長の楕円
        this._graphics.fill(0x8b4513); // SaddleBrown

        // 首/頭 (右側)
        this._graphics.circle(12, 0, 6);
        this._graphics.fill(0x8b4513);

        // 騎手（ヘルメット/勝負服色） - 中央
        this._graphics.circle(0, 0, 11);
        this._graphics.fill(this._color);
        this._graphics.stroke({ width: 2, color: 0x333333 });
    }

    // アニメーション更新
    public update(_delta: number, speed: number) {
        // 速度に応じてボビング（上下動＝スケール伸縮）させる
        // speed が大きいほど速く動く
        if (speed > 0.1) {
            const freq = Date.now() / 100 * (speed * 0.5);
            const scaleY = 1 + Math.sin(freq) * 0.05;
            this.scale.set(1, scaleY);
        } else {
            this.scale.set(1, 1);
        }
    }

    // 位置更新用メソッド（将来拡張用）
    public updatePosition(x: number, y: number) {
        this.x = x;
        this.y = y;
    }
}
