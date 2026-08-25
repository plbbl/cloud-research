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
const greetingCopy = document.querySelector(".greeting p");
const modeButtons = [...document.querySelectorAll(".mode")];
const navModeButtons = [...document.querySelectorAll("[data-nav-mode]")];
const expertLabels = [...document.querySelectorAll(".team li")];
const suggestionButtons = [...document.querySelectorAll("[data-suggestion]")];

let mode = "research";
let backgroundResearch = false;
let hasConversation = false;
let working = false;
const streamedEntries = new Map();

const modeCopy = {
  research: {
    title: "What should the lab pursue?",
    subtitle: "One brief gives you a persistent team of six AI researchers.",
    placeholder: "Describe the field, question, compute, and what a useful handoff should contain",
    hint: "The Director chooses the experts and keeps the work moving.",
    workspace: "New research",
    conversation: "Research shift",
    send: "Start research",
  },
  explain: {
    title: "What should we make clear?",
    subtitle: "Bring a paper, result, or research question. Explainer will rebuild the logic.",
    placeholder: "Paste the paper, abstract, result, or question you want to understand",
    hint: "Explainer separates the claim, evidence, uncertainty, and next move.",
    workspace: "New explanation",
    conversation: "Explanation",
    send: "Start explanation",
  },
};

fetch("/api/about")
  .then((response) => response.json())
  .then((about) => {
    backgroundResearch = Boolean(about.background_research);
    executionMode.textContent = backgroundResearch ? "Runs in Cloud" : "Live session";
    workspaceState.textContent = backgroundResearch ? "Google Cloud ready" : "Local workspace";
  })
  .catch(() => {
    executionMode.textContent = "Live session";
    workspaceState.textContent = "Local workspace";
  });

function setMode(nextMode, focus = false) {
  mode = nextMode;
  modeButtons.forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
  navModeButtons.forEach((button) =>
    button.classList.toggle("active", button.dataset.navMode === mode),
  );

  const copy = modeCopy[mode];
  startTitle.textContent = copy.title;
  greetingCopy.textContent = copy.subtitle;
  brief.placeholder = copy.placeholder;
  promptHint.textContent = copy.hint;
  send.setAttribute("aria-label", copy.send);
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

function startNewResearch(nextMode = "research") {
  if (working) return;
  hasConversation = false;
  streamedEntries.clear();
  transcript.replaceChildren();
  markAgent("");
  conversation.hidden = true;
  conversationDock.hidden = true;
  startScreen.hidden = false;
  startDock.prepend(form);
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
  conversationMode.textContent = modeCopy[mode].conversation;
  conversationTitle.textContent = raw.length > 82 ? `${raw.slice(0, 79)}...` : raw;
  workspaceName.textContent = mode === "research" ? "Active research" : "Active explanation";
  addEntry("You", raw, "human");
  brief.value = "";
  brief.style.height = "";
  window.scrollTo({ top: 0, behavior: "instant" });
}

function setWorking(nextWorking) {
  working = nextWorking;
  document.body.classList.toggle("working", working);
  form.setAttribute("aria-busy", String(working));
  send.disabled = working;
  brief.readOnly = working;
  workspaceState.textContent = working
    ? "Research team working"
    : backgroundResearch
      ? "Google Cloud ready"
      : "Local workspace";
}

function markAgent(author = "") {
  const normalized = author.toLowerCase();
  expertLabels.forEach((label) => {
    label.classList.toggle("active", normalized.includes(label.dataset.agent));
  });
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

function renderEvent(line) {
  if (!line.startsWith("data:")) return;
  const event = JSON.parse(line.slice(5).trim());
  if (event.error) throw new Error(event.error);
  const author = event.author || "Research Director";
  const text = eventText(event);
  if (!text) return;
  markAgent(`${author} ${text}`);
  const isTool = text.startsWith("Calling ") || text.startsWith("Evidence returned");
  upsertStreamedEntry(event, author, text, isTool ? "tool" : "assistant");
}

async function runResearch(prompt) {
  const sessionId = crypto.randomUUID();
  const userId = "human-pi";
  const appName = "app";

  const session = await fetch(`/apps/${appName}/users/${userId}/sessions/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  if (!session.ok) throw new Error(`Could not open the research lab (${session.status}).`);

  const request = await fetch("/run_sse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      appName,
      userId,
      sessionId,
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

async function dispatchResearch(prompt) {
  const response = await fetch("/api/dispatch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief: prompt }),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || `Cloud Run returned ${response.status}.`);
  addEntry("Cloud Run", result.message);
  addEntry("Operation", result.operation, "tool");
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
  markAgent("Research Director");
  const prompt =
    mode === "explain"
      ? `Ask Explainer to make this genuinely understandable, then stop:\n\n${raw}`
      : `Take over this research program and return the strongest evidence-backed handoff:\n\n${raw}`;

  try {
    if (backgroundResearch && mode === "research") {
      await dispatchResearch(prompt);
    } else {
      await runResearch(prompt);
      addEntry("Cloud Research", "Handoff complete. The next decision belongs to you.");
    }
  } catch (error) {
    addEntry("Service", error.message || String(error), "error");
  } finally {
    markAgent("");
    setWorking(false);
    brief.focus();
  }
});

setMode("research");
