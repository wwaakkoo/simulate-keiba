/**
 * レース選択セレクトボックス
 */
import type { RaceListItem } from "../../types";

interface RaceSelectorProps {
    races: RaceListItem[];
    selectedRaceId: string;
    onSelect: (raceId: string) => void;
    disabled: boolean;
}

export const RaceSelector = ({
    races,
    selectedRaceId,
    onSelect,
    disabled,
}: RaceSelectorProps) => (
    <select
        value={selectedRaceId}
        onChange={(e) => onSelect(e.target.value)}
        disabled={disabled}
        className="sim-select"
    >
        {races.map((race) => (
            <option key={race.race_id} value={race.race_id}>
                [{race.date}] {race.venue} {race.name} ({race.distance}m)
            </option>
        ))}
    </select>
);
