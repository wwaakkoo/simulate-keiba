/**
 * レース情報パネル（コース情報・注記）
 */
import type { RaceDetailResponse } from "../../types";

interface RaceInfoProps {
    raceDetail: RaceDetailResponse;
}

export const RaceInfo = ({ raceDetail }: RaceInfoProps) => {
    // Grade dummy detection (if name contains G1 etc)
    const getGrade = (name: string) => {
        if (name.includes("G1")) return "G1";
        if (name.includes("G2")) return "G2";
        if (name.includes("G3")) return "G3";
        return null; // or open
    };
    const grade = getGrade(raceDetail.name);

    return (
        <div className="sim-race-info">
            <div className="sim-race-info__header">
                <div className="sim-race-info__title-row">
                    <h2>
                        {raceDetail.name}
                        {grade && <span className="sim-race-info__grade">{grade}</span>}
                    </h2>
                    <div className="sim-race-info__subtitle">
                        <span>🐎 {raceDetail.venue} {raceDetail.distance}m</span>
                        <span>{raceDetail.course_type}</span>
                        {raceDetail.weather && <span>⛅ {raceDetail.weather}</span>}
                        {raceDetail.track_condition && <span>🏟️ {raceDetail.track_condition}</span>}
                    </div>
                </div>
            </div>

            <div className="sim-divider" style={{ width: "100%", height: "1px", margin: "12px 0", opacity: 0.2 }} />

            <p className="sim-race-info__note" style={{ display: "flex", justifyContent: "space-between" }}>
                <span>{raceDetail.date} 発走</span>
                <span className="text-muted" style={{ fontSize: "12px" }}>Simulation Speed: Adaptive</span>
            </p>
        </div>
    );
};
