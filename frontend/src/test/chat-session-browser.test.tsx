/**
 * Tests for SessionBrowser (chat-tab left rail) and ChatTabShell.
 *
 * Covers:
 *  1. Renders preset folder tree from the mocked API.
 *  2. Preset folders have NO delete option in their ⋯ menu.
 *  3. Custom folders DO have a delete option.
 *  4. Pinned section appears when a session is pinned.
 *  5. ChatTabShell renders the shell structure (browser + conversation).
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

// ── Mock the chatSessions API ────────────────────────────────────────────
vi.mock("../api/chatSessions", () => ({
  getChatTree: vi.fn(),
  createSession: vi.fn(),
  updateSession: vi.fn(),
  deleteSession: vi.fn(),
  createFolder: vi.fn(),
  updateFolder: vi.fn(),
  deleteFolder: vi.fn(),
  reorderSessions: vi.fn(),
}));

// ── Mock DiscoverHomePage so ChatTabShell test is lightweight ────────────
vi.mock("../pages/student/DiscoverHomePage", () => ({
  default: () => <div data-testid="discover-home-page">Uni conversation</div>,
}));

// ── Mock chatTemplates so NewSessionLauncher loads without hitting the API ─
vi.mock("../api/chatTemplates", () => ({
  getChatTemplates: vi.fn().mockResolvedValue([]),
}));
vi.mock("../api/programs", () => ({
  searchPrograms: vi.fn().mockResolvedValue({ items: [] }),
}));
vi.mock("../api/scholarships", () => ({
  searchScholarships: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1 }),
}));

// ── Other mocks expected by the module tree ──────────────────────────────
vi.mock("../api/discovery", () => ({
  listSessions: vi.fn().mockResolvedValue([]),
  getSession: vi.fn().mockResolvedValue(null),
  startUnifiedSession: vi.fn().mockResolvedValue({ id: "s1", track: "discovery", started_at: "" }),
  appendMessage: vi.fn().mockResolvedValue({ student_message: null, assistant_message: null }),
  getCompletionMap: vi.fn().mockResolvedValue({ profile: "0", goals: "0", needs: "0", identity: "0" }),
  getHandoffVerdict: vi.fn().mockResolvedValue({ should_handoff: false, handoff_target: null, reason: "", completion: {} }),
}));
vi.mock("../api/livingProfile", () => ({
  getLivingProfile: vi.fn().mockResolvedValue({ narrative: "", lightsUp: [], goals: [], needs: [], gaps: [] }),
  updateSignal: vi.fn(),
}));
vi.mock("../stores/auth-store", () => ({
  useAuthStore: (sel: (s: { user: { email: string; uni_guided: boolean } }) => unknown) =>
    sel({ user: { email: "test@unipaith.co", uni_guided: false } }),
}));
vi.mock("../stores/toast-store", () => ({ showToast: vi.fn() }));
vi.mock("../api/connect", () => ({ getUnseenCount: vi.fn().mockResolvedValue(0) }));
vi.mock("../api/inbox", () => ({ getThreads: vi.fn().mockResolvedValue([]) }));

import { getChatTree } from "../api/chatSessions";
import { getChatTemplates } from "../api/chatTemplates";
import { searchPrograms } from "../api/programs";
import { searchScholarships } from "../api/scholarships";
import SessionBrowser from "../pages/student/chat/SessionBrowser";
import ChatTabShell from "../pages/student/chat/ChatTabShell";

// ── Sample tree data ─────────────────────────────────────────────────────
const SAMPLE_TREE = {
  folders: [
    {
      id: "f-custom-1",
      name: "Reach schools",
      kind: "custom" as const,
      topic_key: null,
      stage: null,
      sort_order: 0,
      sessions: [
        { id: "s-1", title: "MIT", pinned: false, sort_order: 0, folder_id: "f-custom-1", origin_kind: "manual", topic_key: null },
        { id: "s-2", title: "Stanford", pinned: true, sort_order: 1, folder_id: "f-custom-1", origin_kind: "manual", topic_key: null },
      ],
    },
    {
      id: "f-profile",
      name: "Profile",
      kind: "preset" as const,
      topic_key: "profile",
      stage: "discovery",
      sort_order: 1,
      sessions: [
        { id: "s-3", title: "Your story", pinned: false, sort_order: 0, folder_id: "f-profile", origin_kind: "manual", topic_key: "profile" },
      ],
    },
    {
      id: "f-goals",
      name: "Goals",
      kind: "preset" as const,
      topic_key: "goals",
      stage: "discovery",
      sort_order: 2,
      sessions: [],
    },
    {
      id: "f-schools",
      name: "Schools",
      kind: "preset" as const,
      topic_key: "schools",
      stage: "recommendation",
      sort_order: 3,
      sessions: [],
    },
  ],
};

function renderBrowser(props = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SessionBrowser {...props} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// ── Tests ────────────────────────────────────────────────────────────────

describe("SessionBrowser", () => {
  beforeEach(() => {
    vi.mocked(getChatTree).mockResolvedValue(SAMPLE_TREE);
  });

  it("renders the search box and action buttons", async () => {
    renderBrowser();
    expect(await screen.findByPlaceholderText("Search sessions")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new session/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new folder/i })).toBeInTheDocument();
  });

  it("renders folders from the API", async () => {
    renderBrowser();
    // Custom folder
    expect(await screen.findByText("Reach schools")).toBeInTheDocument();
    // Preset folder (discovery stage)
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Goals")).toBeInTheDocument();
    // Preset folder (recommendation stage)
    expect(screen.getByText("Schools")).toBeInTheDocument();
  });

  it("renders stage group labels for preset folders", async () => {
    renderBrowser();
    expect(await screen.findByText("Discovery")).toBeInTheDocument();
    expect(screen.getByText("Recommendation")).toBeInTheDocument();
    // Application group not in sample, so not rendered
    expect(screen.queryByText("Application Strategy & Support")).not.toBeInTheDocument();
  });

  it("shows a Pinned section when sessions are pinned", async () => {
    renderBrowser();
    // Stanford is pinned in sample data
    expect(await screen.findByText("Pinned")).toBeInTheDocument();
  });

  it("does NOT show Pinned section when no sessions are pinned", async () => {
    const treeNoPins = {
      folders: [
        {
          id: "f-custom-1",
          name: "My folder",
          kind: "custom" as const,
          topic_key: null,
          stage: null,
          sort_order: 0,
          sessions: [
            { id: "s-1", title: "Session A", pinned: false, sort_order: 0, folder_id: "f-custom-1", origin_kind: "manual", topic_key: null },
          ],
        },
      ],
    };
    vi.mocked(getChatTree).mockResolvedValue(treeNoPins);
    renderBrowser();
    await screen.findByText("My folder");
    expect(screen.queryByText("Pinned")).not.toBeInTheDocument();
  });

  it("preset folder ⋯ menu has NO delete or rename option", async () => {
    renderBrowser();
    // Wait for folders to render
    await screen.findByText("Profile");

    // Open the ⋯ menu on the Profile preset folder
    const profileFolder = screen.getByText("Profile").closest("[role='button']")!;
    const menuBtn = profileFolder.querySelector("[aria-label='Profile folder options']");
    if (!menuBtn) {
      // Menu button may not be directly in the heading — find by aria-label in scope
      const btn = screen
        .getAllByRole("button")
        .find((b) => b.getAttribute("aria-label") === "Profile folder options");
      expect(btn).toBeDefined();
      fireEvent.click(btn!);
    } else {
      fireEvent.click(menuBtn);
    }

    await waitFor(() => {
      // Preset menu should have "New session here" but NOT "Delete" or "Rename"
      expect(screen.getByRole("menuitem", { name: /new session here/i })).toBeInTheDocument();
      expect(screen.queryByRole("menuitem", { name: /delete/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("menuitem", { name: /rename/i })).not.toBeInTheDocument();
    });
  });

  it("custom folder ⋯ menu HAS delete option", async () => {
    renderBrowser();
    await screen.findByText("Reach schools");

    const btn = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("aria-label") === "Reach schools folder options");
    expect(btn).toBeDefined();
    fireEvent.click(btn!);

    await waitFor(() => {
      expect(screen.getByRole("menuitem", { name: /delete folder/i })).toBeInTheDocument();
      expect(screen.getByRole("menuitem", { name: /rename/i })).toBeInTheDocument();
    });
  });

  it("session ⋯ menu has rename, pin, delete", async () => {
    renderBrowser();
    await screen.findByText("Your story");

    const btn = screen
      .getAllByRole("button")
      .find((b) => b.getAttribute("aria-label") === "Session options");
    expect(btn).toBeDefined();
    fireEvent.click(btn!);

    await waitFor(() => {
      expect(screen.getByRole("menuitem", { name: /rename/i })).toBeInTheDocument();
      expect(screen.getByRole("menuitem", { name: /pin/i })).toBeInTheDocument();
      expect(screen.getByRole("menuitem", { name: /delete/i })).toBeInTheDocument();
    });
  });

  it("filters sessions by search text", async () => {
    renderBrowser();
    await screen.findByText("MIT");

    const input = screen.getByPlaceholderText("Search sessions");
    fireEvent.change(input, { target: { value: "MIT" } });

    await waitFor(() => {
      // MIT matches; Stanford should not be visible as a session row
      expect(screen.getByText("MIT")).toBeInTheDocument();
      // "Stanford" session row gone (still in Pinned? no — search hides non-matching)
      // The word "Stanford" as a session row inside a folder should be hidden
      expect(screen.queryByText("Stanford")).not.toBeInTheDocument();
    });
  });
});

describe("ChatTabShell", () => {
  beforeEach(() => {
    vi.mocked(getChatTree).mockResolvedValue({ folders: [] });
    vi.mocked(getChatTemplates).mockResolvedValue([]);
    vi.mocked(searchPrograms).mockResolvedValue({ items: [] });
    vi.mocked(searchScholarships).mockResolvedValue({ items: [], total: 0, page: 1 });
  });

  it("renders the session browser aside and the new-session launcher by default", async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <ChatTabShell />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    // With no active session, the launcher is shown (not the conversation)
    expect(
      await screen.findByRole("heading", { name: /where would you like to start/i }),
    ).toBeInTheDocument();
    // The conversation is NOT yet visible
    expect(screen.queryByTestId("discover-home-page")).not.toBeInTheDocument();
    // Session browser aside (accessible label)
    expect(screen.getByRole("complementary", { name: /session browser/i })).toBeInTheDocument();
  });

  it("hides templates that include unavailable action steps", async () => {
    vi.mocked(getChatTemplates).mockResolvedValue([
      {
        key: "build_school_list",
        title: "Build my school list",
        topic: "schools",
        stage: "recommendation",
        outcome: "A ranked list",
        icon: "list",
        steps: [
          {
            step_order: 0,
            step_type: "action",
            action_key: "build_school_list",
            label: "List",
            action_label: "Build school list",
            action_available: true,
          },
        ],
      },
      {
        key: "find_events",
        title: "Find events",
        topic: "connect",
        stage: "application",
        outcome: "Events to attend",
        icon: "calendar",
        steps: [
          {
            step_order: 0,
            step_type: "action",
            action_key: "find_events",
            label: "Events",
            action_label: "Find events",
            action_available: false,
            availability_reason: "This guided action is not enabled for release yet.",
          },
        ],
      },
    ]);

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <ChatTabShell />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText("Build my school list")).toBeInTheDocument();
    expect(screen.queryByText("Find events")).not.toBeInTheDocument();
  });

  it("shows a retryable template error without blocking regular chat actions", async () => {
    vi.mocked(getChatTemplates).mockRejectedValue(new Error("catalog unavailable"));

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <ChatTabShell />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(
      await screen.findByText("Templates couldn't load.", undefined, { timeout: 4000 }),
    ).toBeInTheDocument();
    expect(screen.getByText("You can still start a regular chat.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /build your school list/i })).toBeInTheDocument();
  });

  it("shows academic and scholarship fetch failures while keeping fallback actions visible", async () => {
    vi.mocked(searchPrograms).mockRejectedValue(new Error("programs unavailable"));
    vi.mocked(searchScholarships).mockRejectedValue(new Error("scholarships unavailable"));

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <ChatTabShell />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(
      await screen.findByText("Programs couldn't load.", undefined, { timeout: 4000 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Scholarships couldn't load.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /search programs/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /find more scholarships/i })).toBeInTheDocument();
  });
});
