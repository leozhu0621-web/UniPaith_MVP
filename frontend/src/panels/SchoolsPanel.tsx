import { useState, type FormEvent } from "react";
import { apiFetch } from "../api";

export default function SchoolsPanel() {
  const [response, setResponse] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [fetchId, setFetchId] = useState("");

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

  const NUM_FIELDS = [
    "acceptance_rate",
    "sat_avg",
    "act_avg",
    "enrollment",
    "tuition_in_state",
    "tuition_out_state",
    "graduation_rate",
    "retention_rate",
  ] as const;

  function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const body: Record<string, unknown> = {};

    for (const [k, v] of fd.entries()) {
      const s = (v as string).trim();
      if (s === "") continue;

      if ((NUM_FIELDS as readonly string[]).includes(k)) {
        body[k] = Number(s);
      } else if (["programs", "current_preferences", "historical_stats"].includes(k)) {
        try {
          body[k] = JSON.parse(s);
        } catch {
          body[k] = s;
        }
      } else {
        body[k] = s;
      }
    }

    call(() => apiFetch("/schools", { method: "POST", body: JSON.stringify(body) }));
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* ---- Left: inputs ---- */}
      <div className="space-y-6 overflow-auto max-h-[85vh]">
        <section>
          <h2 className="font-semibold mb-2">Create School</h2>
          <form onSubmit={handleCreate} className="space-y-2">
            <Field name="name" label="Name *" required />
            <Field name="acceptance_rate" label="Acceptance Rate (0-1)" type="number" step="0.001" />
            <Field name="sat_avg" label="SAT Avg" type="number" />
            <Field name="act_avg" label="ACT Avg" type="number" />
            <Field name="enrollment" label="Enrollment" type="number" />
            <Field name="tuition_in_state" label="Tuition (In-State)" type="number" />
            <Field name="tuition_out_state" label="Tuition (Out-of-State)" type="number" />
            <Field name="graduation_rate" label="Graduation Rate (0-1)" type="number" step="0.001" />
            <Field name="retention_rate" label="Retention Rate (0-1)" type="number" step="0.001" />
            <Field name="state" label="State" />
            <Field name="region" label="Region" />
            <Field name="locale" label="Locale" />
            <Field name="ownership" label="Ownership" />
            <Area name="description" label="Description" />
            <Area name="programs" label="Programs (JSON)" rows={3} placeholder='["CS","Biology"]' />
            <Area name="current_preferences" label="Current Preferences (JSON)" rows={3} placeholder='{"min_gpa":3.0}' />
            <Area name="historical_stats" label="Historical Stats (JSON)" rows={3} placeholder='{"avg_gpa":3.5}' />
            <button type="submit" disabled={loading} className="px-3 py-1.5 bg-gray-900 text-white rounded text-sm disabled:opacity-40">
              Create
            </button>
          </form>
        </section>

        <section className="border-t pt-4">
          <h2 className="font-semibold mb-2">Fetch School</h2>
          <div className="flex gap-2">
            <input
              value={fetchId}
              onChange={(e) => setFetchId(e.target.value)}
              placeholder="School ID"
              className="border rounded px-2 py-1 text-sm flex-1"
            />
            <button
              onClick={() => call(() => apiFetch(`/schools/${fetchId}`))}
              disabled={!fetchId || loading}
              className="px-3 py-1.5 bg-gray-900 text-white rounded text-sm disabled:opacity-40"
            >
              Fetch
            </button>
          </div>
          <button
            onClick={() => call(() => apiFetch("/schools?limit=50&offset=0"))}
            disabled={loading}
            className="mt-2 px-3 py-1.5 border rounded text-sm disabled:opacity-40"
          >
            List All
          </button>
        </section>
      </div>

      {/* ---- Right: output ---- */}
      <ResponsePane loading={loading} error={error} data={response} />
    </div>
  );
}

function Field(props: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  const { label, ...rest } = props;
  return (
    <label className="block">
      <span className="text-sm text-gray-600">{label}</span>
      <input {...rest} className="block w-full border rounded px-2 py-1 text-sm mt-0.5" />
    </label>
  );
}

function Area(
  props: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string },
) {
  const { label, ...rest } = props;
  return (
    <label className="block">
      <span className="text-sm text-gray-600">{label}</span>
      <textarea {...rest} rows={rest.rows ?? 3} className="block w-full border rounded px-2 py-1 text-sm mt-0.5" />
    </label>
  );
}

function ResponsePane({ loading, error, data }: { loading: boolean; error: string | null; data: unknown }) {
  return (
    <div className="border rounded p-3 bg-white overflow-auto max-h-[80vh]">
      {loading && <p className="text-sm text-gray-500">Loading…</p>}
      {error && <p className="text-sm text-red-600 whitespace-pre-wrap">{error}</p>}
      {data !== null && !loading && (
        <>
          {Array.isArray(data) && (
            <p className="text-xs text-gray-500 mb-1">{data.length} result(s)</p>
          )}
          <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>
        </>
      )}
    </div>
  );
}
