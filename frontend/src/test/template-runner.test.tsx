/**
 * TemplateRunner — vitest tests.
 *
 * Covers:
 *  1. Renders the work-order spine with the correct number of steps.
 *  2. Renders the first step's prompt question from the embedded descriptor.
 *  3. Renders a "choice" widget (AnswerChoices) when ask_kind === "choice".
 *  4. Advances to the next step after a choice is picked.
 *  5. Renders an action step placeholder (not a real result).
 *  6. Shows the completion card when all steps are done.
 *  7. Calls onClose when "Save to My Space" is clicked.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

// ── Mock dependencies ────────────────────────────────────────────────────────

vi.mock("../api/chatTemplates", () => ({
  getChatTemplates: vi.fn(),
}));

vi.mock("../api/enrichment", () => ({
  setEnrichValue: vi.fn().mockResolvedValue({}),
  getEnrichNext: vi.fn().mockResolvedValue({ items: [], essentials_present: true }),
}));

// EnrichWidget uses countries list — stub the named exports used by TemplateRunner
vi.mock("../components/student/EnrichWidget", () => ({
  KeywordPicker: ({ onSubmit }: { onSubmit: (v: string[]) => void }) => (
    <button onClick={() => onSubmit(["option1"])}>keyword-picker</button>
  ),
  TypeaheadPicker: ({ onSubmit }: { onSubmit: (v: string) => void }) => (
    <button onClick={() => onSubmit("United States")}>typeahead-picker</button>
  ),
}));

import { getChatTemplates } from "../api/chatTemplates";
import { setEnrichValue } from "../api/enrichment";
import TemplateRunner from "../pages/student/chat/TemplateRunner";

// ── Sample template data ──────────────────────────────────────────────────────

const SAMPLE_TEMPLATE = {
  key: "set_your_goals",
  title: "Set your goals",
  topic: "goals",
  stage: "discovery",
  outcome: "Your goal stack",
  icon: "flag",
  steps: [
    {
      step_order: 0,
      step_type: "prompt" as const,
      prompt_key: "career_goal",
      label: "Career",
      question: "What kind of work do you see yourself in?",
      ask_kind: "keywords" as const,
      options: ["Software / tech", "Finance", "Consulting"],
    },
    {
      step_order: 1,
      step_type: "prompt" as const,
      prompt_key: "target_degree_level",
      label: "Direction",
      question: "What degree are you aiming for?",
      ask_kind: "choice" as const,
      options: ["Bachelor's", "Master's", "Ph.D."],
    },
    {
      step_order: 2,
      step_type: "action" as const,
      action_key: "generate_goal_stack",
      label: "Your stack",
      action_label: "Generate goal stack",
    },
  ],
};

// ── Helper ───────────────────────────────────────────────────────────────────

function renderRunner(templateKey = "set_your_goals", onClose = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <TemplateRunner templateKey={templateKey} onClose={onClose} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// ── Helper: advance past both prompt steps to reach the action step ───────────

async function advanceThroughPromptSteps() {
  // Step 1: keywords picker
  await screen.findByText("What kind of work do you see yourself in?");
  fireEvent.click(screen.getByText("keyword-picker"));
  // Step 2: choice
  await waitFor(() => screen.getByText("What degree are you aiming for?"));
  fireEvent.click(screen.getByText("Bachelor's"));
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("TemplateRunner", () => {
  beforeEach(() => {
    vi.mocked(getChatTemplates).mockResolvedValue([SAMPLE_TEMPLATE]);
    vi.mocked(setEnrichValue).mockResolvedValue({});
  });

  it("renders the template title and step count", async () => {
    renderRunner();
    expect(await screen.findByText("Set your goals")).toBeInTheDocument();
    expect(screen.getByText("Step 1 of 3")).toBeInTheDocument();
  });

  it("renders the work-order spine with all step labels", async () => {
    renderRunner();
    await screen.findByText("Set your goals");
    expect(screen.getByRole("listitem", { name: /step 1.*career/i })).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: /step 2.*direction/i })).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: /step 3.*your stack/i })).toBeInTheDocument();
  });

  it("renders the first step's question from the embedded descriptor", async () => {
    renderRunner();
    expect(
      await screen.findByText("What kind of work do you see yourself in?"),
    ).toBeInTheDocument();
  });

  it("renders the keywords widget for the first step (ask_kind=keywords)", async () => {
    renderRunner();
    await screen.findByText("What kind of work do you see yourself in?");
    // KeywordPicker is mocked as a button with text "keyword-picker"
    expect(screen.getByText("keyword-picker")).toBeInTheDocument();
  });

  it("advances to the next step after submitting the keyword picker", async () => {
    renderRunner();
    await screen.findByText("What kind of work do you see yourself in?");
    fireEvent.click(screen.getByText("keyword-picker"));

    await waitFor(() => {
      // Should now show step 2's question
      expect(
        screen.getByText("What degree are you aiming for?"),
      ).toBeInTheDocument();
    });
  });

  it("calls setEnrichValue with the submitted value", async () => {
    renderRunner();
    await screen.findByText("What kind of work do you see yourself in?");
    fireEvent.click(screen.getByText("keyword-picker"));

    await waitFor(() => {
      expect(vi.mocked(setEnrichValue)).toHaveBeenCalledWith("career_goal", ["option1"]);
    });
  });

  it("renders choice options for a choice-type step", async () => {
    // Start from step 2 (choice step) by auto-advancing past step 1.
    renderRunner();
    await screen.findByText("What kind of work do you see yourself in?");
    // Advance past step 1
    fireEvent.click(screen.getByText("keyword-picker"));

    await waitFor(() => {
      expect(screen.getByText("What degree are you aiming for?")).toBeInTheDocument();
    });

    // Choice options for step 2 should be visible
    expect(screen.getByText("Bachelor's")).toBeInTheDocument();
    expect(screen.getByText("Master's")).toBeInTheDocument();
  });

  it("renders an action step with placeholder text, not fake school data", async () => {
    renderRunner();
    await advanceThroughPromptSteps();

    // Now on the action step — "generate goal stack" appears in framing + placeholder
    await waitFor(() => {
      expect(screen.getAllByText(/generate goal stack/i).length).toBeGreaterThan(0);
    });

    // Should NOT contain anything that looks like made-up school data
    expect(screen.queryByText(/carnegie mellon/i)).not.toBeInTheDocument();
  });

  it("shows the completion card after all steps finish", async () => {
    renderRunner();
    await advanceThroughPromptSteps();

    // Wait for the action step's 2-second timer to fire (real timers)
    await waitFor(
      () => screen.getByRole("button", { name: /continue/i }),
      { timeout: 4000 },
    );
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(screen.getByText("Your goal stack")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /save to my space/i }),
      ).toBeInTheDocument();
    });
  });

  it("calls onClose when Save to My Space is clicked", async () => {
    const onClose = vi.fn();
    renderRunner("set_your_goals", onClose);

    await advanceThroughPromptSteps();

    await waitFor(
      () => screen.getByRole("button", { name: /continue/i }),
      { timeout: 4000 },
    );
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() =>
      screen.getByRole("button", { name: /save to my space/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: /save to my space/i }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("shows an error state when the template key is not found", async () => {
    renderRunner("nonexistent_key");
    await waitFor(() => {
      expect(
        screen.getByText(/template "nonexistent_key" not found/i),
      ).toBeInTheDocument();
    });
  });
});
