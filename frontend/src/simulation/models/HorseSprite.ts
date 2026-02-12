import { Container, Graphics, Text, TextStyle } from 'pixi.js';

const HORSE_RADIUS = 15;
const COLORS: Record<number, number> = {
    1: 0xffffff, // 白
    2: 0x000000, // 黒
    3: 0xff0000, // 赤
    4: 0x0000ff, // 青
    5: 0xffff00, // 黄
    6: 0x008000, // 緑
    7: 0xffa500, // 橙
    8: 0xffc0cb, // 桃
};

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

        // 馬体（円）
        this._graphics = new Graphics();
        this.drawHorse();
        this.addChild(this._graphics);

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
        this._graphics.circle(0, 0, HORSE_RADIUS);
        this._graphics.fill(this._color);
        this._graphics.stroke({ width: 2, color: 0x333333 });
    }

    // 位置更新用メソッド（将来拡張用）
    public updatePosition(x: number, y: number) {
        this.x = x;
        this.y = y;
    }
}
