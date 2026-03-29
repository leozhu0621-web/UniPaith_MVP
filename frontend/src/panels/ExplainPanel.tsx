import { useState } from "react";
import { apiFetch } from "../api";

interface ExplainResponse {
  match_id: string;
  student_id: string;
  school_id: string;
  school_name: string;
  tier: string;
  calibrated_probability: number;
  explanation: string;
}

export default function ExplainPanel() {
  const [response, setResponse] = useState<ExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [matchId, setMatchId] = useState("");

  async function handleExplain() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<ExplainResponse>(`/explain/${matchId}`);
      setResponse(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* ---- Left: input ---- */}
      <div>
        <h2 className="font-semibold mb-2">Explain Match</h2>
        <div className="flex gap-2">
          <input
            value={matchId}
            onChange={(e) => setMatchId(e.target.value)}
            placeholder="Match ID"
            className="border rounded px-2 py-1 text-sm flex-1"
          />
          <button
            onClick={handleExplain}
            disabled={!matchId || loading}
            className="px-3 py-1.5 bg-gray-900 text-white rounded text-sm disabled:opacity-40"
          >
            Explain
          </button>
        </div>
      </div>

      {/* ---- Right: output ---- */}
      <div className="border rounded p-3 bg-white overflow-auto max-h-[80vh]">
        {loading && <p className="text-sm text-gray-500">Loading…</p>}
        {error && <p className="text-sm text-red-600 whitespace-pre-wrap">{error}</p>}

        {response && !loading && (
          <>
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
              <p className="text-xs text-gray-500 mb-1">
                {response.school_name} &middot; {response.tier} &middot;{" "}
                {(response.calibrated_probability * 100).toFixed(1)}%
              </p>
              <p className="text-sm leading-relaxed">{response.explanation}</p>
            </div>
            <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(response, null, 2)}</pre>
          </>
        )}
      </div>
    </div>
  );
}
