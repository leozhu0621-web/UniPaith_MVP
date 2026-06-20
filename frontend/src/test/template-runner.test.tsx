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
  dispatchTemplateAction: vi.fn(),
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

import { getChatTemplates, dispatchTemplateAction } from "../api/chatTemplates";
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
      action_available: true,
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
    vi.clearAllMocks();
    vi.mocked(getChatTemplates).mockResolvedValue([SAMPLE_TEMPLATE]);
    vi.mocked(setEnrichValue).mockResolvedValue({});
    // Default: pending artifact (safe for tests that don't care about the specific result)
    vi.mocked(dispatchTemplateAction).mockResolvedValue({
      action_key: "generate_goal_stack",
      kind: "note",
      title: "Generate goal stack",
      summary: "Your profile needs a bit more information before we can generate a goal stack.",
      status: "pending",
    });
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

    // Now on the action step — "generate goal stack" appears in framing
    await waitFor(() => {
      expect(screen.getAllByText(/generate goal stack/i).length).toBeGreaterThan(0);
    });

    // Should NOT contain anything that looks like made-up school data
    expect(screen.queryByText(/carnegie mellon/i)).not.toBeInTheDocument();
  });

  it("shows the action artifact card after the API call resolves", async () => {
    renderRunner();
    await advanceThroughPromptSteps();

    // Artifact card resolves after API call — "Continue" button appears
    await waitFor(
      () => screen.getByRole("button", { name: /continue/i }),
      { timeout: 3000 },
    );
    expect(vi.mocked(dispatchTemplateAction)).toHaveBeenCalledWith("generate_goal_stack");
    // The artifact card title should be visible (it appears in the card header)
    expect(screen.getByText("Generate goal stack")).toBeInTheDocument();
    expect(screen.getByText(/needs a bit more information/i)).toBeInTheDocument();
    expect(screen.getByText("Saved")).toBeInTheDocument();
    expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
  });

  it("does not dispatch unavailable action steps", async () => {
    vi.mocked(getChatTemplates).mockResolvedValue([
      {
        ...SAMPLE_TEMPLATE,
        steps: [
          {
            step_order: 0,
            step_type: "action" as const,
            action_key: "find_events",
            label: "Events",
            action_label: "Find events",
            action_available: false,
            availability_reason: "This guided action is not enabled for release yet.",
          },
        ],
      },
    ]);

    renderRunner();

    await waitFor(
      () => screen.getByText("This guided action is not enabled for release yet."),
      { timeout: 3000 },
    );
    expect(vi.mocked(dispatchTemplateAction)).not.toHaveBeenCalled();
    expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
  });

  it("renders a school_list artifact with items when status=ready", async () => {
    // Override: return a school_list artifact with items
    vi.mocked(dispatchTemplateAction).mockResolvedValue({
      action_key: "build_school_list",
      kind: "school_list",
      title: "Your starter list",
      items: [
        { name: "MIT", program: "Computer Science", fit_label: "Great fit", odds_label: "Reach" },
        { name: "Stanford", program: "CS", fit_label: "Good fit", odds_label: "Competitive" },
      ],
      status: "ready",
    });

    // Use a template with only a build_school_list action step
    vi.mocked(getChatTemplates).mockResolvedValue([
      {
        ...SAMPLE_TEMPLATE,
        steps: [
          {
            step_order: 0,
            step_type: "action" as const,
            action_key: "build_school_list",
            label: "School list",
            action_label: "Build school list",
            action_available: true,
          },
        ],
      },
    ]);

    renderRunner();
    // The artifact title appears once the API call resolves
    await waitFor(
      () => screen.getByText("Your starter list"),
      { timeout: 3000 },
    );

    // Artifact items should appear
    expect(screen.getByText("MIT")).toBeInTheDocument();
    expect(screen.getByText("Great fit")).toBeInTheDocument();
    expect(screen.getByText("Reach")).toBeInTheDocument();
  });

  it("shows the completion card after all steps finish", async () => {
    renderRunner();
    await advanceThroughPromptSteps();

    // Wait for the action artifact card (API resolves immediately in tests)
    await waitFor(
      () => screen.getByRole("button", { name: /continue/i }),
      { timeout: 3000 },
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
      { timeout: 3000 },
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
