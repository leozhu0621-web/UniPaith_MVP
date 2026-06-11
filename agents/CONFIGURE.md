# Configuring "Uni" on the Claude Agent Platform — Manual

A step-by-step guide to standing Uni up on **platform.claude.com** (the Console).
Two paths are given: **A) the Console** (click-through, where you are now) and
**B) the `ant` CLI** (version-controlled, recommended for production). Both create
the same agent.

> **Read this first — the one thing that surprises everyone.** Uni's five tools
> are **host-side custom tools**: when she calls `search_programs`,
> `get_profile_snapshot`, etc., the platform **pauses the session and waits for
> YOUR backend to answer**. That means you cannot fully chat with Uni in the
> Console alone — the moment she calls a tool, the session goes idle until the
> UniPaith host (`services/uni_agent_host.py`) returns a result. The Console is
> for **creating, configuring, versioning, and watching** Uni. **Real
> conversations require the backend host running.** (Building that host is the
> separate implementation plan.)

---

## What you already have

- **Workspace:** `wrkspc_01BsNHs7kyh9aJF1xq5Eqrdh`
- **Environment:** `UniPaith_MVP` → `env_01N43sA3tmVhij3YYZgWzAP2` (Cloud, limited
  networking, MCP + package access enabled). **No changes needed** — Uni's tools
  run on your host, so the container never needs network access. Leave it as is.

---

## Path A — Configure in the Console (click-through)

### Step 1 — Create the agent
Console → **Agents** → **Create agent** → start from **Blank**.

### Step 2 — Name + description
- **Name:** `Uni — UniPaith Counselor`
- **Description:** paste the block from [§ Paste-ready: Description](#paste-ready-description) below.

### Step 3 — Model
- **Model:** **Claude Opus 4.8** (`claude-opus-4-8`). Speed: standard.
- Leave thinking at its default — managed agents run with extended thinking on by
  default; there's nothing to toggle. Do not downgrade the model; the counselor
  *is* the product.

### Step 4 — System prompt (the persona)
Paste the entire contents of **`agents/uni_system.md`** (also reproduced in
[§ Paste-ready: System prompt](#paste-ready-system-prompt)) into the **System
prompt / Instructions** field.

### Step 5 — Tools (critical)
1. **Do NOT add the built-in agent toolset** (no bash / file / web). Uni is a
   pure conversational counselor. If the Blank template added a toolset, remove
   it (or disable every tool in it).
2. **Add five custom tools.** For each, click **Add tool → Custom tool** and fill
   in the name, description, and JSON input schema from
   [§ Paste-ready: The five tools](#paste-ready-the-five-tools):
   - `get_profile_snapshot`
   - `search_programs`
   - `save_signals`
   - `get_matches`
   - `generate_strategy`

   (The source of truth for these is `agents/uni.agent.yaml` — copy the schemas
   from there if the Console wants raw JSON.)

### Step 6 — Save → record the IDs
Save the agent. Record:
- **`agent_id`** (`agent_…`) — shown on the agent page / returned on save.
- **`version`** — every save bumps this; pin it for reproducibility.

Put both, plus the env id, into your backend config (see Step 8).

### Step 7 — Generate an API key for the backend
Console → **Settings → API keys → Create key** (scope it to this workspace).
Store it as `ANTHROPIC_API_KEY` in the backend secret store (it likely already
exists for the rest of the app — reuse it if so). **The backend holds this key;
students never see it.**

### Step 8 — Wire the backend
In `unipaith-backend` config (env vars / Secrets Manager):
```
UNI_AGENT_ID=agent_…            # from Step 6
UNI_ENVIRONMENT_ID=env_01N43sA3tmVhij3YYZgWzAP2
ANTHROPIC_API_KEY=…             # from Step 7 (probably already set)
AI_UNI_MANAGED_AGENT_V1=true    # the new flag that routes conversation to Uni
```
The host (`services/uni_agent_host.py`) reads these to create and drive sessions.

### Step 9 — Smoke-test (with the caveat)
Console → open the agent → **Start session** (pick `UniPaith_MVP`) → send
"Hi, I'm thinking about grad school." You'll see Uni reply and then **emit a
`get_profile_snapshot` / `search_programs` tool call and go idle** — that's
correct. To get past it you need the backend host answering tool calls; in the
Console alone the session will wait. Watch the event stream to confirm her tool
calls look right (correct tool, sensible inputs).

---

## Path B — Configure with the `ant` CLI (version-controlled, recommended for prod)

Define Uni in git and apply from CI, so her brain config is reviewed in PRs and
rolls back like code.

```sh
# Install + auth (once)
brew install anthropics/tap/ant
ant auth login --workspace-id wrkspc_01BsNHs7kyh9aJF1xq5Eqrdh

# Create the agent from the checked-in YAML; capture the id
AGENT_ID=$(ant beta:agents create < agents/uni.agent.yaml --transform id -r)
echo "UNI_AGENT_ID=$AGENT_ID"

# Iterate later (every edit to uni.agent.yaml / uni_system.md = a new version):
ant beta:agents update --agent-id "$AGENT_ID" --version <CURRENT_N> < agents/uni.agent.yaml
```

`agents/uni.agent.yaml` already omits the agent toolset and declares the five
custom tools; `system: "@./uni_system.md"` inlines the persona. The environment
already exists, so you don't recreate it — just pass its id when starting
sessions (the host does this).

---

## "Training" Uni after she's live (configure + evaluate — no ML)

1. **Watch** real sessions in the Console (or your event mirror in
   `discovery_messages`).
2. **Spot** a weak turn — she fabricated, recommended too early, missed a needs cue.
3. **Tweak** `uni_system.md` (or a tool description).
4. **Re-run the eval suite** — the §61/§62 harness (`constitution_student.md`
   rubric + eval cases + the deterministic crisis/no-fabrication/grounding
   floors that gate in CI with no API key).
5. If it improves and the floors still pass, **bump the version** (Step 6 / `ant
   update`) and deploy. Pin sessions to a known-good version; roll back instantly
   if a change regresses.

---

## Paste-ready: Description

```
Warm, knowledgeable college-admissions counselor — "everyone's private college counselor." Leads each student through a guided Discovery → Recommendation → Application journey, grounds every claim in UniPaith's real program catalog, remembers what she learns, and hands off to a personalized first look at matches. Never sounds like a search engine.
```

## Paste-ready: System prompt

→ Use the full contents of **`agents/uni_system.md`** (same directory as this
file). It's the single source of truth; paste it verbatim into the System prompt
field.

## Paste-ready: The five tools

→ Copy the `tools:` block from **`agents/uni.agent.yaml`**. Each entry has the
exact `name`, `description`, and `input_schema` to paste into the Console's
"Add custom tool" form (the Console may want the schema as raw JSON — the YAML
maps 1:1 to JSON).

| Tool | Input | What your host returns |
|---|---|---|
| `get_profile_snapshot` | _(none)_ | profile + goals + needs + identity + active strategy + completion |
| `search_programs` | query + optional country / degree_types / tuition / formats / location | grounded program facts (name, school, degree, tuition, deadline, outcomes) |
| `save_signals` | basic / personality / identity / goals / needs | written counts + updated completion + `handoff_ready` |
| `get_matches` | _(none)_ | top programs with fitness, confidence, band, rationale |
| `generate_strategy` | _(none)_ | career → degree → academic/financial/geographic paths + narrative |
