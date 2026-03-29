import { useState } from "react";
import { apiFetch } from "../api";

interface MatchRow {
  school_id?: string;
  student_id?: string;
  school_name?: string;
  raw_score?: number;
  calibrated_probability?: number;
  tier?: string;
}

export default function MatchingPanel() {
  const [response, setResponse] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [s2sStudentId, setS2sStudentId] = useState("");
  const [s2sTopK, setS2sTopK] = useState("10");

  const [sc2stSchoolId, setSc2stSchoolId] = useState("");
  const [sc2stTopK, setSc2stTopK] = useState("50");

  const [discoverSchoolId, setDiscoverSchoolId] = useState("");
  const [discoverTopK, setDiscoverTopK] = useState("20");

  async function call(fn: () => Promise<unknown>) {
    setLoading(true);
    setError(null);
    try {
      setResponse(await fn());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const matchRows: MatchRow[] = Array.isArray(response) ? response : [];

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* ---- Left: inputs ---- */}
      <div className="space-y-6">
        {/* Student → Schools */}
        <section>
          <h2 className="font-semibold mb-2">Student → Schools</h2>
          <div className="space-y-2">
            <input
              value={s2sStudentId}
              onChange={(e) => setS2sStudentId(e.target.value)}
              placeholder="Student ID"
              className="border rounded px-2 py-1 text-sm w-full"
            />
            <input
              value={s2sTopK}
              onChange={(e) => setS2sTopK(e.target.value)}
              type="number"
              placeholder="top_k"
              className="border rounded px-2 py-1 text-sm w-32"
            />
            <button
              onClick={() =>
                call(() =>
                  apiFetch("/match/student-to-schools", {
                    method: "POST",
                    body: JSON.stringify({ student_id: s2sStudentId, top_k: Number(s2sTopK) }),
                  }),
                )
              }
              disabled={!s2sStudentId}
              className="block px-3 py-1.5 bg-gray-900 text-white rounded text-sm disabled:opacity-40"
            >
              Match
            </button>
          </div>
        </section>

        {/* School → Students */}
        <section className="border-t pt-4">
          <h2 className="font-semibold mb-2">School → Students</h2>
          <div className="space-y-2">
            <input
              value={sc2stSchoolId}
              onChange={(e) => setSc2stSchoolId(e.target.value)}
              placeholder="School ID"
              className="border rounded px-2 py-1 text-sm w-full"
            />
            <input
              value={sc2stTopK}
              onChange={(e) => setSc2stTopK(e.target.value)}
              type="number"
              placeholder="top_k"
              className="border rounded px-2 py-1 text-sm w-32"
            />
            <button
              onClick={() =>
                call(() =>
                  apiFetch("/match/school-to-students", {
                    method: "POST",
                    body: JSON.stringify({ school_id: sc2stSchoolId, top_k: Number(sc2stTopK) }),
                  }),
                )
              }
              disabled={!sc2stSchoolId}
              className="block px-3 py-1.5 bg-gray-900 text-white rounded text-sm disabled:opacity-40"
            >
              Match
            </button>
          </div>
        </section>

        {/* Discover */}
        <section className="border-t pt-4">
          <h2 className="font-semibold mb-2">Discover</h2>
          <div className="space-y-2">
            <input
              value={discoverSchoolId}
              onChange={(e) => setDiscoverSchoolId(e.target.value)}
              placeholder="School ID"
              className="border rounded px-2 py-1 text-sm w-full"
            />
            <input
              value={discoverTopK}
              onChange={(e) => setDiscoverTopK(e.target.value)}
              type="number"
              placeholder="top_k"
              className="border rounded px-2 py-1 text-sm w-32"
            />
            <button
              onClick={() =>
                call(() =>
                  apiFetch("/discover", {
                    method: "POST",
                    body: JSON.stringify({ school_id: discoverSchoolId, top_k: Number(discoverTopK) }),
                  }),
                )
              }
              disabled={!discoverSchoolId}
              className="block px-3 py-1.5 bg-gray-900 text-white rounded text-sm disabled:opacity-40"
            >
              Discover
            </button>
          </div>
        </section>
      </div>

      {/* ---- Right: output ---- */}
      <div className="border rounded p-3 bg-white overflow-auto max-h-[80vh]">
        {loading && <p className="text-sm text-gray-500">Loading…</p>}
        {error && <p className="text-sm text-red-600 whitespace-pre-wrap">{error}</p>}

        {matchRows.length > 0 && !loading && (
          <table className="w-full text-xs border-collapse mb-4">
            <thead>
              <tr className="border-b text-left">
                <th className="py-1 pr-2">Name / ID</th>
                <th className="py-1 pr-2">Score</th>
                <th className="py-1 pr-2">Tier</th>
                <th className="py-1">Probability</th>
              </tr>
            </thead>
            <tbody>
              {matchRows.map((r, i) => (
                <tr key={i} className="border-b">
                  <td className="py-1 pr-2">{r.school_name ?? r.school_id ?? r.student_id ?? "—"}</td>
                  <td className="py-1 pr-2">{r.raw_score?.toFixed(4) ?? "—"}</td>
                  <td className="py-1 pr-2">{r.tier ?? "—"}</td>
                  <td className="py-1">{r.calibrated_probability != null ? (r.calibrated_probability * 100).toFixed(1) + "%" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {response !== null && !loading && (
          <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(response, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}
