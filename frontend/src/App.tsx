import { useState } from "react";
import StudentsPanel from "./panels/StudentsPanel";
import SchoolsPanel from "./panels/SchoolsPanel";
import MatchingPanel from "./panels/MatchingPanel";
import ExplainPanel from "./panels/ExplainPanel";

const TABS = ["students", "schools", "matching", "explain"] as const;
type Tab = (typeof TABS)[number];

export default function App() {
  const [tab, setTab] = useState<Tab>("students");

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white px-4 py-3 flex items-center gap-6">
        <h1 className="text-lg font-semibold">UniPaith MVP</h1>
        <nav className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded text-sm capitalize ${
                tab === t
                  ? "bg-gray-900 text-white"
                  : "hover:bg-gray-100"
              }`}
            >
              {t}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex-1 p-4">
        {tab === "students" && <StudentsPanel />}
        {tab === "schools" && <SchoolsPanel />}
        {tab === "matching" && <MatchingPanel />}
        {tab === "explain" && <ExplainPanel />}
      </main>
    </div>
  );
}
