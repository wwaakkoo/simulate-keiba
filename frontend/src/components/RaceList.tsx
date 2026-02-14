import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { raceApi } from "../api/raceApi";
import type { RaceListItem } from "../types";

export const RaceList = () => {
    const [races, setRaces] = useState<RaceListItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [page, setPage] = useState(1);
    const ITEMS_PER_PAGE = 20;

    useEffect(() => {
        const loadData = async () => {
            try {
                const data = await raceApi.getRaces();
                // Default sort: Date desc
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

    // Filter
    const filteredRaces = useMemo(() => {
        if (!searchTerm) return races;
        const lower = searchTerm.toLowerCase();
        return races.filter(r =>
            r.name.toLowerCase().includes(lower) ||
            r.venue.includes(searchTerm) ||
            r.date.includes(searchTerm)
        );
    }, [races, searchTerm]);

    // Pagination
    const totalPages = Math.ceil(filteredRaces.length / ITEMS_PER_PAGE);
    const paginatedRaces = useMemo(() => {
        const start = (page - 1) * ITEMS_PER_PAGE;
        return filteredRaces.slice(start, start + ITEMS_PER_PAGE);
    }, [filteredRaces, page]);

    const courseTypeColor = (type: string) => {
        if (type.includes("芝")) return "text-success";
        if (type.includes("ダ")) return "text-warning";
        return "text-sub";
    };

    return (
        <div className="app-container p-4 max-w-6xl mx-auto">
            <header className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold mb-1">Race Archive</h1>
                    <p className="text-muted text-sm">Browse all collected race data</p>
                </div>
                <div className="flex gap-4">
                    <Link to="/" className="btn btn-ghost">Back to Dashboard</Link>
                </div>
            </header>

            {/* Search & Filter Bar */}
            <div className="card mb-6 flex gap-4 items-center">
                <input
                    type="text"
                    placeholder="Search races (Name, Venue, Date)..."
                    className="sim-select flex-1"
                    value={searchTerm}
                    onChange={(e) => {
                        setSearchTerm(e.target.value);
                        setPage(1); // Reset to page 1 on search
                    }}
                />
                <div className="text-muted text-sm">
                    {filteredRaces.length} races found
                </div>
            </div>

            {/* Race Table */}
            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                {loading ? (
                    <div className="p-8 text-center text-muted">Loading race archive...</div>
                ) : (
                    <>
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
                                {paginatedRaces.map((race) => (
                                    <tr key={race.race_id} style={{ borderTop: "1px solid var(--color-border)" }} className="hover:bg-surface-hover transition-colors">
                                        <td className="p-4 text-main font-mono text-sm">{race.date}</td>
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
                                            <div className="flex justify-end gap-2">
                                                {/* Detail Page Link */}
                                                <Link
                                                    to={`/races/${race.race_id}`}
                                                    className="btn btn-ghost text-xs"
                                                >
                                                    Details
                                                </Link>
                                                <Link
                                                    to={`/simulation?raceId=${race.race_id}`}
                                                    className="btn btn-primary text-xs"
                                                >
                                                    Simulate
                                                </Link>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {paginatedRaces.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="p-8 text-center text-muted">
                                            No races found matching "{searchTerm}"
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>

                        {/* Pagination */}
                        <div className="p-4 border-t border-[var(--color-border)] flex justify-between items-center">
                            <button
                                className="btn btn-ghost text-sm"
                                disabled={page === 1}
                                onClick={() => setPage(p => p - 1)}
                            >
                                « Previous
                            </button>
                            <span className="text-sm text-muted">
                                Page {page} of {totalPages || 1}
                            </span>
                            <button
                                className="btn btn-ghost text-sm"
                                disabled={page >= totalPages}
                                onClick={() => setPage(p => p + 1)}
                            >
                                Next »
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
