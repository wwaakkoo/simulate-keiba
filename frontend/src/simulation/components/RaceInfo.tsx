/**
 * レース情報パネル（コース情報・注記）
 */
import type { RaceDetailResponse } from "../../types";

interface RaceInfoProps {
    raceDetail: RaceDetailResponse;
}

export const RaceInfo = ({ raceDetail }: RaceInfoProps) => (
    <div className="sim-race-info">
        <div className="sim-race-info__header">
            <span>
                🚩 {raceDetail.venue} {raceDetail.distance}m {raceDetail.course_type}
            </span>
            <span className="sim-race-info__note">
                ※ 現在のシミュレーション速度は目安です
            </span>
        </div>
        <p className="sim-race-info__desc">
            オーバルコースでの走行シミュレーションです。脚質（逃げ・差し等）に合わせて速度配分が調整されます。
        </p>
    </div>
);
