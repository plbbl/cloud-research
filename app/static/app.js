const form = document.querySelector("#research-form");
const brief = document.querySelector("#research-brief");
const send = document.querySelector("#send");
const promptHint = document.querySelector("#prompt-hint");
const executionMode = document.querySelector("#execution-mode");
const startScreen = document.querySelector("#start-screen");
const startDock = document.querySelector("#start-dock");
const conversation = document.querySelector("#conversation");
const conversationDock = document.querySelector("#conversation-dock");
const conversationMode = document.querySelector("#conversation-mode");
const conversationTitle = document.querySelector("#conversation-title");
const transcript = document.querySelector("#transcript");
const workspaceName = document.querySelector("#workspace-name");
const workspaceState = document.querySelector("#workspace-state");
const startTitle = document.querySelector("#start-title");
const greetingCopy = document.querySelector(".greeting > p");
const explainTargets = document.querySelector("#explain-targets");
const labPresence = document.querySelector("#lab-presence");
const labAgent = document.querySelector("#lab-agent");
const labAction = document.querySelector("#lab-action");
const heroLabSlot = document.querySelector("#hero-lab-slot");
const conversationLabSlot = document.querySelector("#conversation-lab-slot");
const modeButtons = [...document.querySelectorAll(".mode")];
const navModeButtons = [...document.querySelectorAll("[data-nav-mode]")];
const explainTargetButtons = [...document.querySelectorAll("[data-explain-target]")];
const expertLabels = [...document.querySelectorAll(".team li")];
const suggestionButtons = [...document.querySelectorAll("[data-suggestion]")];

const APP_NAME = "app";
const USER_ID = "human-pi";

let mode = "research";
let explainTarget = "paper";
let backgroundResearch = false;
let backgroundActive = false;
let hasConversation = false;
let working = false;
let activeSessionId = "";
let sessionReady = false;
let activeExpert = "";
let currentLabState = "idle";
let runPollTimer = 0;
let runPollToken = 0;
let latestResearchOutput = "";
const streamedEntries = new Map();
const seenRunEvents = new Set();

const agentPresence = {
  director: {
    name: "Research Director",
    state: "directing",
    action: "Director is assembling the expert panel",
  },
  cloud_research: {
    name: "Research Director",
    state: "directing",
    action: "Director is choosing the strongest next move",
  },
  finder: {
    name: "Finder",
    state: "searching",
    action: "Finder is mapping prior work",
  },
  theorist: {
    name: "Theorist",
    state: "theorizing",
    action: "Theorist is sharpening the mechanism",
  },
  experimentalist: {
    name: "Experimentalist",
    state: "testing",
    action: "Experimentalist is running a decisive probe",
  },
  critic: {
    name: "Critic",
    state: "critiquing",
    action: "Critic is attacking the strongest claim",
  },
  writer: {
    name: "Writer",
    state: "writing",
    action: "Writer is assembling the research handoff",
  },
  explainer: {
    name: "Explainer",
    state: "explaining",
    action: "Explainer is rebuilding the logic for you",
  },
};

const modeCopy = {
  research: {
    title: "What should the lab pursue?",
    subtitle: "One brief gives you a persistent team of six AI researchers.",
    placeholder: "Describe the field, question, compute, and a useful research handoff",
    hint: "The Director chooses the experts and keeps the work moving.",
    workspace: "New research",
    conversation: "Research shift",
    send: "Start research",
  },
  explain: {
    title: "What should we make clear?",
    subtitle: "Explainer turns papers, tasks, and results into working understanding.",
    placeholder: "Paste what you want to understand",
    hint: "Choose what you are bringing to the lab.",
    workspace: "New explanation",
    conversation: "Explanation",
    send: "Start explanation",
  },
};

const explainCopy = {
  paper: {
    placeholder: "Paste a paper title, abstract, link, or passage",
    hint: "Explainer will rebuild the paper from prior belief to next experiment.",
  },
  task: {
    placeholder: "Describe the research task, benchmark, or open question",
    hint: "Explainer will expose the real objective, difficulty, novelty, and cheapest test.",
  },
  research: {
    placeholder: "Ask about the research this lab has produced",
    hint: "Explainer will connect the claim, evidence, failures, and strongest next move.",
  },
  result: {
    placeholder: "Paste a result, metric, table, log, or surprising failure",
    hint: "Explainer will separate what the result proves from what it only suggests.",
  },
};

const explainPrompts = {
  paper:
    "Ask Explainer only. Rebuild this paper: prior belief, new mechanism, evidence, limits, one vivid example, and next test. Then stop.",
  task:
    "Ask Explainer only. Make this task operational: objective, real difficulty, nearest work, novelty, cheapest decisive test, and what success teaches. Then stop.",
  research:
    "Ask Explainer only. Explain our research as one causal story: claim, evidence, failed paths, uncertainty, and the next move. Then stop.",
  result:
    "Ask Explainer only. Interpret this result: what happened, why it matters, what it proves, what it does not prove, and the next discriminating test. Then stop.",
};

fetch("/api/about")
  .then((response) => response.json())
  .then((about) => {
    backgroundResearch = Boolean(about.background_research);
    executionMode.textContent = backgroundResearch ? "Runs in Cloud" : "Live session";
    refreshWorkspaceState();
  })
  .catch(() => {
    executionMode.textContent = "Live session";
    workspaceState.textContent = "Local workspace";
  });

function normalizeAgent(value = "") {
  const normalized = value.toLowerCase().replaceAll("-", "_").replaceAll(" ", "_");
  if (agentPresence[normalized]) return normalized;
  return Object.keys(agentPresence).find((agent) => normalized.includes(agent)) || "director";
}

function setLabState(agent = "director", state = "", detail = "") {
  const normalizedAgent = normalizeAgent(agent);
  const presence = agentPresence[normalizedAgent] || agentPresence.director;
  const nextState = state || presence.state;

  if (activeExpert && activeExpert !== normalizedAgent && agentPresence[activeExpert]) {
    const previous = expertLabels.find((label) => label.dataset.agent === activeExpert);
    if (previous) previous.querySelector("small").textContent = "Complete";
  }

  expertLabels.forEach((label) => label.classList.remove("active"));
  const activeLabel = expertLabels.find((label) => label.dataset.agent === normalizedAgent);
  if (activeLabel && !["complete", "error", "idle"].includes(nextState)) {
    activeLabel.classList.add("active");
    activeLabel.querySelector("small").textContent = detail || presence.action;
    activeExpert = normalizedAgent;
  } else if (["complete", "error"].includes(nextState)) {
    if (activeLabel) {
      activeLabel.querySelector("small").textContent =
        nextState === "complete" ? "Complete" : "Needs attention";
    }
    activeExpert = "";
  }

  currentLabState = nextState;
  labPresence.dataset.state = nextState;
  if (nextState === "complete") {
    labAgent.textContent = "Handoff ready";
    labAction.textContent = detail || "The expert panel has returned its strongest result";
  } else if (nextState === "error") {
    labAgent.textContent = "Lab needs attention";
    labAction.textContent = detail || "The current shift could not continue";
  } else if (nextState === "idle") {
    labAgent.textContent = "Lab ready";
    labAction.textContent = detail || "Six experts are standing by";
  } else {
    labAgent.textContent = presence.name;
    labAction.textContent = detail || presence.action;
  }
  refreshWorkspaceState();
}

function resetLab() {
  activeExpert = "";
  labPresence.dataset.idleVariant = String(Math.floor(Math.random() * 4));
  expertLabels.forEach((label) => {
    label.classList.remove("active");
    label.querySelector("small").textContent = "Ready";
  });
  setLabState("director", "idle", "Six experts are standing by");
}

function refreshWorkspaceState() {
  if (working) workspaceState.textContent = "Research team working";
  else if (backgroundActive) workspaceState.textContent = "Lab running in Google Cloud";
  else if (currentLabState === "complete") workspaceState.textContent = "Handoff ready";
  else if (backgroundResearch) workspaceState.textContent = "Google Cloud ready";
  else workspaceState.textContent = "Local workspace";
}

function updateExplainTarget(nextTarget) {
  explainTarget = nextTarget;
  explainTargetButtons.forEach((button) => {
    const active = button.dataset.explainTarget === explainTarget;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  if (mode === "explain") {
    brief.placeholder = explainCopy[explainTarget].placeholder;
    promptHint.textContent = explainCopy[explainTarget].hint;
  }
}

function setMode(nextMode, focus = false) {
  mode = nextMode;
  modeButtons.forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
  navModeButtons.forEach((button) =>
    button.classList.toggle("active", button.dataset.navMode === mode),
  );
  suggestionButtons.forEach((button) => {
    button.hidden = button.dataset.suggestionMode !== mode;
  });
  explainTargets.hidden = mode !== "explain";

  const copy = modeCopy[mode];
  startTitle.textContent = copy.title;
  greetingCopy.textContent = copy.subtitle;
  brief.placeholder = copy.placeholder;
  promptHint.textContent = copy.hint;
  send.setAttribute("aria-label", copy.send);
  conversationMode.textContent = copy.conversation;
  executionMode.textContent =
    mode === "research" && backgroundResearch ? "Runs in Cloud" : "Live session";
  if (mode === "explain") updateExplainTarget(explainTarget);
  if (!hasConversation) workspaceName.textContent = copy.workspace;
  if (focus) brief.focus();
}

function closeSidebar() {
  document.body.classList.remove("sidebar-visible");
}

document.querySelector("#sidebar-open").addEventListener("click", () => {
  document.body.classList.add("sidebar-visible");
});
document.querySelector("#sidebar-close").addEventListener("click", closeSidebar);
document.querySelector("#sidebar-scrim").addEventListener("click", closeSidebar);

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode, true));
});

navModeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    startNewResearch(button.dataset.navMode);
    closeSidebar();
  });
});

explainTargetButtons.forEach((button) => {
  button.addEventListener("click", () => {
    updateExplainTarget(button.dataset.explainTarget);
    brief.focus();
  });
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setMode(button.dataset.suggestionMode);
    brief.value = button.dataset.suggestion;
    resizeComposer();
    brief.focus();
  });
});

document.querySelector("#new-research").addEventListener("click", () => {
  startNewResearch("research");
  closeSidebar();
});

brief.addEventListener("input", resizeComposer);
brief.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (brief.value.trim() && !working) form.requestSubmit();
  }
});

function resizeComposer() {
  brief.style.height = "auto";
  brief.style.height = `${Math.min(brief.scrollHeight, 190)}px`;
}

function stopRunPolling() {
  runPollToken += 1;
  window.clearTimeout(runPollTimer);
  runPollTimer = 0;
  backgroundActive = false;
}

function startNewResearch(nextMode = "research") {
  if (working) return;
  stopRunPolling();
  hasConversation = false;
  activeSessionId = "";
  sessionReady = false;
  latestResearchOutput = "";
  streamedEntries.clear();
  seenRunEvents.clear();
  transcript.replaceChildren();
  resetLab();
  conversation.hidden = true;
  conversationDock.hidden = true;
  startScreen.hidden = false;
  startDock.prepend(form);
  heroLabSlot.append(labPresence);
  brief.value = "";
  brief.style.height = "";
  setMode(nextMode, true);
}

function openConversation(raw) {
  hasConversation = true;
  streamedEntries.clear();
  startScreen.hidden = true;
  conversation.hidden = false;
  conversationDock.hidden = false;
  conversationDock.append(form);
  conversationLabSlot.append(labPresence);
  conversationMode.textContent = modeCopy[mode].conversation;
  conversationTitle.textContent = raw.length > 82 ? `${raw.slice(0, 79)}...` : raw;
  workspaceName.textContent = mode === "research" ? "Active research" : "Active explanation";
  addEntry("You", raw, "human");
  brief.value = "";
  brief.style.height = "";
  window.scrollTo({ top: 0, behavior: "auto" });
}

function setWorking(nextWorking) {
  working = nextWorking;
  document.body.classList.toggle("working", working || backgroundActive);
  form.setAttribute("aria-busy", String(working));
  send.disabled = working;
  brief.readOnly = working;
  refreshWorkspaceState();
}

function addEntry(author, text, kind = "assistant") {
  if (!text) return;
  const { entry, body } = createEntry(author, kind);
  body.textContent = text;
  entry.scrollIntoView({ behavior: "smooth", block: "end" });
}

function createEntry(author, kind) {
  const entry = document.createElement("article");
  entry.className = `message ${kind}`;

  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = author.replaceAll("_", " ");

  const body = document.createElement("p");
  body.className = "message-body";

  entry.append(label, body);
  transcript.append(entry);
  return { entry, body };
}

function upsertStreamedEntry(event, author, text, kind) {
  const key = event.id || `${event.invocationId}:${author}:${kind}`;
  let streamed = streamedEntries.get(key);
  if (!streamed) {
    streamed = createEntry(author, kind);
    streamedEntries.set(key, streamed);
  }

  if (event.partial === true) streamed.body.textContent += text;
  else {
    streamed.body.textContent = text;
    streamedEntries.delete(key);
  }
  streamed.entry.scrollIntoView({ behavior: "smooth", block: "end" });
}

function eventText(event) {
  const parts = event.content?.parts || [];
  return parts
    .map((part) => {
      if (part.text) return part.text;
      if (part.functionCall?.name) return `Calling ${part.functionCall.name}`;
      if (part.functionResponse?.name) return `Evidence returned by ${part.functionResponse.name}`;
      return "";
    })
    .filter(Boolean)
    .join("\n");
}

function showLivePresence(event) {
  const parts = event.content?.parts || [];
  const calledAgent = parts.find((part) => part.functionCall?.name)?.functionCall?.name;
  if (calledAgent) {
    const agent = normalizeAgent(calledAgent);
    const presence = agentPresence[agent];
    setLabState(agent, presence.state, presence.action);
    return;
  }
  const author = normalizeAgent(event.author || "director");
  if (author !== "director" || event.author === "cloud_research") {
    const presence = agentPresence[author];
    setLabState(author, presence.state, presence.action);
  }
}

function renderEvent(line) {
  if (!line.startsWith("data:")) return;
  const event = JSON.parse(line.slice(5).trim());
  if (event.error) throw new Error(event.error);
  const author = event.author || "Research Director";
  const text = eventText(event);
  if (!text) return;
  showLivePresence(event);
  const isTool = text.startsWith("Calling ") || text.startsWith("Evidence returned");
  upsertStreamedEntry(event, author, text, isTool ? "tool" : "assistant");
}

async function ensureLiveSession() {
  if (sessionReady && activeSessionId) return;
  activeSessionId = activeSessionId || crypto.randomUUID();
  const session = await fetch(
    `/apps/${APP_NAME}/users/${USER_ID}/sessions/${activeSessionId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    },
  );
  if (!session.ok) throw new Error(`Could not open the research lab (${session.status}).`);
  sessionReady = true;
}

async function runResearch(prompt) {
  await ensureLiveSession();
  const request = await fetch("/run_sse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      appName: APP_NAME,
      userId: USER_ID,
      sessionId: activeSessionId,
      streaming: true,
      newMessage: { role: "user", parts: [{ text: prompt }] },
    }),
  });
  if (!request.ok || !request.body) {
    throw new Error(`The research service returned ${request.status}.`);
  }

  const reader = request.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    lines.forEach(renderEvent);
  }
  if (buffer.trim()) renderEvent(buffer);
}

function consumeRunEvent(event) {
  const key = `${event.sequence}:${event.state}:${event.agent}`;
  if (seenRunEvents.has(key)) return;
  seenRunEvents.add(key);
  setLabState(event.agent, event.state, event.detail);

  if (event.state === "complete") {
    backgroundActive = false;
    latestResearchOutput = event.output || "";
    addEntry(
      "Research handoff",
      event.output || "The research shift completed. The handoff is ready in the run logs.",
    );
    document.body.classList.remove("working");
  } else if (event.state === "error") {
    backgroundActive = false;
    addEntry("Research shift", event.output || event.detail, "error");
    document.body.classList.remove("working");
  }
  refreshWorkspaceState();
}

async function pollResearchRun(runId, token) {
  if (token !== runPollToken) return;
  try {
    const response = await fetch(`/api/runs/${runId}`);
    if (!response.ok) throw new Error(`Live status returned ${response.status}`);
    const result = await response.json();
    result.events.forEach(consumeRunEvent);
    if (result.done || token !== runPollToken) return;
    runPollTimer = window.setTimeout(() => pollResearchRun(runId, token), 2200);
  } catch {
    if (token !== runPollToken) return;
    setLabState("director", "directing", "Live status is reconnecting to the research shift");
    runPollTimer = window.setTimeout(() => pollResearchRun(runId, token), 4200);
  }
}

async function dispatchResearch(prompt) {
  const response = await fetch("/api/dispatch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief: prompt }),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || `Cloud Run returned ${response.status}.`);
  addEntry("Cloud Research", result.message);
  backgroundActive = true;
  document.body.classList.add("working");
  setLabState("director", "directing", "Director is opening a persistent research shift");
  const token = ++runPollToken;
  pollResearchRun(result.run_id, token);
}

function buildPrompt(raw) {
  if (mode === "research") {
    return `Take over this research program and return the strongest evidence-backed handoff:\n\n${raw}`;
  }
  const priorResearch =
    explainTarget === "research" && latestResearchOutput
      ? `\n\nCurrent research handoff:\n${latestResearchOutput}`
      : "";
  return `${explainPrompts[explainTarget]}\n\n${raw}${priorResearch}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const raw = brief.value.trim();
  if (!raw || working) return;

  if (!hasConversation) openConversation(raw);
  else {
    addEntry("You", raw, "human");
    brief.value = "";
    brief.style.height = "";
  }

  setWorking(true);
  setLabState("director", "directing", "Director is reading the research brief");
  const prompt = buildPrompt(raw);

  try {
    if (backgroundResearch && mode === "research") {
      await dispatchResearch(prompt);
    } else {
      await runResearch(prompt);
      setLabState(
        mode === "explain" ? "explainer" : "director",
        "complete",
        mode === "explain" ? "The explanation is ready" : "The live handoff is ready",
      );
    }
  } catch (error) {
    setLabState("director", "error", "The current shift could not continue");
    addEntry("Service", error.message || String(error), "error");
  } finally {
    setWorking(false);
    brief.focus();
  }
});

resetLab();
setMode("research");
