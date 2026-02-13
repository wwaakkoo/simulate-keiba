/**
 * PixiJS Application の初期化・破棄を管理するカスタムフック
 */
import { useEffect, useRef } from "react";
import { Application } from "pixi.js";
import { SIMULATION_CONFIG } from "../config";

const { WIDTH, HEIGHT } = SIMULATION_CONFIG;

/**
 * PixiJS Application を初期化し、指定された DOM 要素にマウントする。
 *
 * @returns canvasRef  - PixiJS キャンバスを挿入する div への ref
 * @returns appRef    - 初期化済みの Application への ref（描画レイヤー追加等に使用）
 * @returns isReady   - 初期化完了フラグ
 */
export function usePixiApp() {
    const canvasRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const initializingRef = useRef(false);
    const readyRef = useRef(false);

    useEffect(() => {
        if (!canvasRef.current || appRef.current || initializingRef.current) return;

        initializingRef.current = true;
        const app = new Application();

        app
            .init({
                width: WIDTH,
                height: HEIGHT,
                backgroundColor: 0x2e8b57,
                antialias: true,
                resolution: window.devicePixelRatio || 1,
                autoDensity: true,
            })
            .then(() => {
                if (canvasRef.current) {
                    canvasRef.current.appendChild(app.canvas);
                    appRef.current = app;
                    readyRef.current = true;
                }
                initializingRef.current = false;
            })
            .catch((err: unknown) => {
                // eslint-disable-next-line no-console
                console.error("PixiJS init error", err);
                initializingRef.current = false;
            });

        return () => {
            if (appRef.current) {
                appRef.current.destroy(true, { children: true, texture: true });
                appRef.current = null;
                readyRef.current = false;
            }
        };
    }, []);

    return { canvasRef, appRef } as const;
}
