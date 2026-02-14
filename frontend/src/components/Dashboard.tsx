import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { raceApi } from "../api/raceApi";
import type { RaceListItem } from "../types";

export const Dashboard = () => {
    const [races, setRaces] = useState<RaceListItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const data = await raceApi.getRaces();
                // Sort by date desc
                const sorted = [...data].sort((a, b) =>
                    new Date(b.date).getTime() - new Date(a.date).getTime()
                );
                setRaces(sorted);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        void loadData();
    }, []);

    const courseTypeColor = (type: string) => {
        if (type.includes("芝")) return "text-success";
        if (type.includes("ダ")) return "text-warning";
        return "text-sub";
    };

    return (
        <div className="app">
            {/* Hero Section */}
            <header className="app-header" style={{ marginBottom: "2rem" }}>
                <h1>🏇 Simulate Keiba</h1>
                <p className="app-subtitle" style={{ opacity: 0.8 }}>
                    AI-Powered Race Prediction & Simulation Platform
                </p>
            </header>

            {/* Stats Overview */}
            <div className="flex gap-4" style={{ marginBottom: "2rem" }}>
                <div className="card flex-1">
                    <h3 className="text-muted text-sm">Total Races</h3>
                    <p className="text-3xl font-bold">{races.length}</p>
                </div>
                <div className="card flex-1">
                    <h3 className="text-muted text-sm">Prediction Model</h3>
                    <p className="text-3xl font-bold text-primary">v1.2</p>
                </div>
                <div className="card flex-1">
                    <h3 className="text-muted text-sm">System Status</h3>
                    <div className="flex items-center gap-2 mt-1">
                        <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--color-success)" }}></span>
                        <span className="text-main">Operational</span>
                    </div>
                </div>
            </div>

            <div className="flex flex-col gap-6">
                {/* Actions */}
                <div className="flex justify-between items-center">
                    <h2 className="text-xl">Recent Races</h2>
                    <div className="flex gap-3">
                        <Link to="/races" className="btn btn-ghost">
                            View All Archive
                        </Link>
                        <Link to="/simulation" className="btn btn-primary">
                            Start New Simulation
                        </Link>
                    </div>
                </div>

                {/* Race List */}
                <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                    {loading ? (
                        <div className="p-4 text-center text-muted">Loading races...</div>
                    ) : (
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead className="bg-surface-hover">
                                <tr>
                                    <th className="p-4 text-left text-sm text-muted font-normal">Date</th>
                                    <th className="p-4 text-left text-sm text-muted font-normal">Race Name</th>
                                    <th className="p-4 text-left text-sm text-muted font-normal">Venue</th>
                                    <th className="p-4 text-right text-sm text-muted font-normal">Distance</th>
                                    <th className="p-4 text-right text-sm text-muted font-normal">Entries</th>
                                    <th className="p-4"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {races.slice(0, 10).map((race) => (
                                    <tr key={race.race_id} style={{ borderTop: "1px solid var(--color-border)" }}>
                                        <td className="p-4 text-main">{race.date}</td>
                                        <td className="p-4">
                                            <div className="font-bold">{race.name}</div>
                                            <div className={`text-xs ${courseTypeColor(race.course_type)}`}>
                                                {race.course_type}
                                            </div>
                                        </td>
                                        <td className="p-4 text-sub">{race.venue}</td>
                                        <td className="p-4 text-right text-main">{race.distance}m</td>
                                        <td className="p-4 text-right text-sub">{race.num_entries}</td>
                                        <td className="p-4 text-right">
                                            <Link
                                                to={`/simulation?raceId=${race.race_id}`}
                                                className="btn btn-ghost text-sm"
                                            >
                                                Simulate
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};
