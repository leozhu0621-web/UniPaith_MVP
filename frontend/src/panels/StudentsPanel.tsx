import { useState, type FormEvent } from "react";
import { apiFetch } from "../api";

export default function StudentsPanel() {
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

  function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const body: Record<string, unknown> = {};
    for (const [k, v] of fd.entries()) {
      const s = (v as string).trim();
      if (s === "") continue;
      if (["gpa", "sat_score", "act_score"].includes(k)) {
        body[k] = Number(s);
      } else {
        body[k] = s;
      }
    }
    call(() => apiFetch("/students", { method: "POST", body: JSON.stringify(body) }));
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* ---- Left: inputs ---- */}
      <div className="space-y-6">
        <section>
          <h2 className="font-semibold mb-2">Create Student</h2>
          <form onSubmit={handleCreate} className="space-y-2">
            <Field name="gpa" label="GPA *" type="number" step="0.01" required />
            <Field name="sat_score" label="SAT Score" type="number" />
            <Field name="act_score" label="ACT Score" type="number" />
            <Field name="state" label="State" />
            <Field name="intended_major" label="Intended Major" />
            <Field name="school_type" label="School Type" />
            <Area name="essay" label="Essay" />
            <Area name="activities" label="Activities" />
            <button type="submit" disabled={loading} className="px-3 py-1.5 bg-gray-900 text-white rounded text-sm disabled:opacity-40">
              Create
            </button>
          </form>
        </section>

        <section className="border-t pt-4">
          <h2 className="font-semibold mb-2">Fetch Student</h2>
          <div className="flex gap-2">
            <input
              value={fetchId}
              onChange={(e) => setFetchId(e.target.value)}
              placeholder="Student ID"
              className="border rounded px-2 py-1 text-sm flex-1"
            />
            <button
              onClick={() => call(() => apiFetch(`/students/${fetchId}`))}
              disabled={!fetchId || loading}
              className="px-3 py-1.5 bg-gray-900 text-white rounded text-sm disabled:opacity-40"
            >
              Fetch
            </button>
          </div>
          <button
            onClick={() => call(() => apiFetch("/students?limit=50&offset=0"))}
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

/* ---- tiny shared helpers (kept in-file to stay simple) ---- */

function Field(props: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  const { label, ...rest } = props;
  return (
    <label className="block">
      <span className="text-sm text-gray-600">{label}</span>
      <input {...rest} className="block w-full border rounded px-2 py-1 text-sm mt-0.5" />
    </label>
  );
}

function Area(props: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string }) {
  const { label, ...rest } = props;
  return (
    <label className="block">
      <span className="text-sm text-gray-600">{label}</span>
      <textarea {...rest} rows={3} className="block w-full border rounded px-2 py-1 text-sm mt-0.5" />
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
