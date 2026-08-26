const $ = (selector) => document.querySelector(selector);

const form = $("#research-form");
const brief = $("#research-brief");
const send = $("#send");
const promptHint = $("#prompt-hint");
const executionMode = $("#execution-mode");
const modelName = $("#model-name");
const startScreen = $("#start-screen");
const startDock = $("#start-dock");
const conversation = $("#conversation");
const conversationDock = $("#conversation-dock");
const conversationMode = $("#conversation-mode");
const conversationTitle = $("#conversation-title");
const conversationLabName = $("#conversation-lab-name");
const transcript = $("#transcript");
const workspaceName = $("#workspace-name");
const workspaceState = $("#workspace-state");
const startTitle = $("#start-title");
const greetingCopy = $(".greeting > p");
const explainTargets = $("#explain-targets");
const labPresence = $("#lab-presence");
const labBot = $("#lab-bot");
const labAgent = $("#lab-agent");
const labAction = $("#lab-action");
const heroLabSlot = $("#hero-lab-slot");
const conversationLabSlot = $("#conversation-lab-slot");
const mentionMenu = $("#mention-menu");
const mentionTrigger = $("#mention-trigger");
const labList = $("#lab-list");
const teamList = $("#team-list");
const memberList = $("#member-list");
const agentStack = $("#agent-stack");
const membersToggle = $("#members-toggle");
const membersClose = $("#members-close");
const membersScrim = $("#members-scrim");
const modeButtons = [...document.querySelectorAll(".mode")];
const navModeButtons = [...document.querySelectorAll("[data-nav-mode]")];
const explainTargetButtons = [...document.querySelectorAll("[data-explain-target]")];
const suggestionButtons = [...document.querySelectorAll("[data-suggestion]")];
const newLabButton = $("#new-lab");
const manageLabButton = $("#manage-lab");
const labDialog = $("#lab-dialog");
const labEditor = $("#lab-editor");
const labDialogTitle = $("#lab-dialog-title");
const labNameInput = $("#lab-name");
const labMissionInput = $("#lab-mission");
const agentEditorList = $("#agent-editor-list");
const labEditorError = $("#lab-editor-error");
const deleteLabButton = $("#delete-lab");
const voiceToggle = $("#voice-toggle");

const USER_ID = "human-pi";
const LAB_STORAGE_KEY = "cloud-research-active-lab";
const ACTIVE_RUN_KEY = "cloud-research-active-run";
const LAST_HANDOFF_KEY = "cloud-research-last-handoff";
const RUN_POLL_INTERVAL = 2400;
const DEFAULT_AGENT_COLORS = [
  "#ff5eb1",
  "#a97efe",
  "#a27952",
  "#111111",
  "#00c972",
  "#2a92fe",
  "#ff8a34",
  "#1aa4a7",
];

let labs = [];
let activeLab = null;
let mode = "research";
let explainTarget = "paper";
let backgroundResearch = false;
let textModelName = "Gemini 3.7 Flash";
let liveModelName = "Gemini Live";
let hasConversation = false;
let working = false;
let activeSessionId = "";
let activeExpert = "";
let currentLabState = "idle";
let latestResearchOutput = "";
let mentionOptions = [];
let visibleMentionOptions = [];
let mentionIndex = 0;
let expertLabels = [];
let labMemberButtons = [];
let memberRoles = new Map();
let editingLabId = "";
let editorAgents = [];
const streamedEntries = new Map();
const renderedRunSequences = new Set();

let voiceSocket = null;
let voiceInputContext = null;
let voiceOutputContext = null;
let voiceStream = null;
let voiceProcessor = null;
let voiceOutputAt = 0;
let voiceActive = false;
let voiceHeardSpeech = false;
let voiceSilenceTimer = 0;
let voiceUserEntry = null;
let voiceBotEntry = null;
const voiceSources = new Set();

const modeCopy = {
  research: {
    title: "What should the lab pursue?",
    placeholder: "Message the lab. Type @ to assign a researcher",
    hint: "Message everyone, @ one expert, or speak with the Lab Bot.",
    workspace: "New research",
    conversation: "Research shift",
    send: "Start research",
  },
  explain: {
    title: "What should we make clear?",
    placeholder: "Paste what you want to understand",
    hint: "Choose the material, then @Explainer or invite another expert.",
    workspace: "New explanation",
    conversation: "Explanation",
    send: "Start explanation",
  },
};

const explainCopy = {
  paper: {
    placeholder: "Paste a paper title, abstract, link, or passage",
    hint: "Rebuild the paper from prior belief to its next decisive experiment.",
  },
  task: {
    placeholder: "Describe the research task, benchmark, or open question",
    hint: "Expose the real objective, novelty, difficulty, and cheapest test.",
  },
  research: {
    placeholder: "Ask about the research this lab has produced",
    hint: "Connect the claim, evidence, failures, uncertainty, and next move.",
  },
  result: {
    placeholder: "Paste a result, metric, table, log, or surprising failure",
    hint: "Separate what the result proves from what it only suggests.",
  },
};

const explainPrompts = {
  paper:
    "Rebuild this paper: prior belief, new mechanism, evidence, limits, one vivid example, and next test.",
  task:
    "Make this task operational: objective, real difficulty, nearest work, novelty, cheapest decisive test, and what success teaches.",
  research:
    "Explain our research as one causal story: claim, evidence, failed paths, uncertainty, and the next move.",
  result:
    "Interpret this result: what happened, why it matters, what it proves, what it does not prove, and the next discriminating test.",
};

const defaultPresence = {
  finder: ["searching", "mapping prior work"],
  theorist: ["theorizing", "sharpening the mechanism"],
  experimentalist: ["testing", "running a decisive probe"],
  critic: ["critiquing", "attacking the strongest claim"],
  writer: ["writing", "assembling the research handoff"],
  explainer: ["explaining", "rebuilding the logic for you"],
};

function activeAgents() {
  return activeLab?.agents || [];
}

function agentFor(value = "") {
  const normalized = value.toLowerCase().replaceAll("-", "_").replaceAll(" ", "_");
  if (!activeLab || normalized === activeLab.id || normalized.includes("director")) return null;
  return (
    activeAgents().find((agent) => agent.id === normalized) ||
    activeAgents().find((agent) => normalized.includes(agent.id)) ||
    activeAgents().find((agent) => normalized.includes(agent.name.toLowerCase().replaceAll(" ", "_"))) ||
    null
  );
}

function presenceFor(value = "") {
  const agent = agentFor(value);
  if (!agent) {
    return {
      id: "director",
      name: "Research Director",
      state: "directing",
      action: "choosing the strongest next move",
    };
  }
  const [state, action] = defaultPresence[agent.id] || inferPresence(agent.role);
  return { ...agent, state, action: `${agent.name} is ${action}` };
}

function inferPresence(role) {
  const copy = role.toLowerCase();
  if (/search|paper|prior|find|scout/.test(copy)) return ["searching", "searching live evidence"];
  if (/experiment|test|code|build|run/.test(copy)) return ["testing", "testing the strongest idea"];
  if (/critic|challenge|risk|fals/.test(copy)) return ["critiquing", "challenging the claim"];
  if (/write|report|synth/.test(copy)) return ["writing", "synthesizing the evidence"];
  if (/explain|teach|clar/.test(copy)) return ["explaining", "making the mechanism clear"];
  return ["theorizing", "developing the research opening"];
}

function avatarElement(agent, className = "") {
  const avatar = document.createElement("span");
  avatar.className = `agent-avatar ${agent.id || "everyone"} ${className}`.trim();
  avatar.style.setProperty("--agent-color", agent.color || "#111111");
  avatar.setAttribute("aria-hidden", "true");
  return avatar;
}

function renderLabs() {
  labList.replaceChildren();
  labs.forEach((lab) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "lab-switch";
    button.dataset.labId = lab.id;
    button.classList.toggle("active", lab.id === activeLab?.id);

    const avatars = document.createElement("span");
    avatars.className = "lab-switch-avatars";
    lab.agents.slice(0, 3).forEach((agent) => avatars.append(avatarElement(agent)));

    const copy = document.createElement("span");
    copy.className = "lab-switch-copy";
    const name = document.createElement("strong");
    name.textContent = lab.name;
    const count = document.createElement("small");
    count.textContent = `${lab.agents.length} researcher${lab.agents.length === 1 ? "" : "s"}`;
    copy.append(name, count);
    button.append(avatars, copy);
    labList.append(button);
  });
}

function personButton(agent, location) {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.agent = agent.id;
  button.dataset.mention = agent.name;
  button.className = location === "team" ? "team-member" : "lab-member";
  button.append(avatarElement(agent));
  const copy = document.createElement("span");
  copy.className = "agent-copy";
  const name = document.createElement("strong");
  name.textContent = agent.name;
  const role = document.createElement("small");
  role.textContent = location === "team" ? "Ready" : agent.role;
  copy.append(name, role);
  button.append(copy);
  return button;
}

function mentionButton(name, role, agent) {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.mention = name;
  button.setAttribute("role", "option");
  button.append(avatarElement(agent));
  const copy = document.createElement("span");
  const label = document.createElement("strong");
  label.textContent = name;
  const description = document.createElement("small");
  description.textContent = role;
  copy.append(label, description);
  button.append(copy);
  return button;
}

function renderLabPeople() {
  teamList.replaceChildren();
  memberList.replaceChildren();
  agentStack.replaceChildren();
  mentionMenu.replaceChildren();

  const heading = document.createElement("p");
  heading.textContent = "Assign a lab member";
  mentionMenu.append(heading);
  mentionMenu.append(
    mentionButton(
      "Everyone",
      "Let the Director recruit the strongest panel",
      { id: "everyone", color: "#111111" },
    ),
  );

  activeAgents().forEach((agent) => {
    const item = document.createElement("li");
    item.dataset.agent = agent.id;
    item.append(personButton(agent, "team"));
    teamList.append(item);
    memberList.append(personButton(agent, "members"));
    mentionMenu.append(mentionButton(agent.name, agent.role, agent));
  });
  activeAgents()
    .slice(0, 5)
    .forEach((agent) => agentStack.append(avatarElement(agent)));

  mentionOptions = [...mentionMenu.querySelectorAll("[data-mention]")];
  expertLabels = [...teamList.querySelectorAll("li[data-agent]")];
  labMemberButtons = [...memberList.querySelectorAll(".lab-member[data-agent]")];
  memberRoles = new Map(activeAgents().map((agent) => [agent.id, agent.role]));
}

function renderActiveLab() {
  if (!activeLab) return;
  renderLabs();
  renderLabPeople();
  conversationLabName.textContent = activeLab.name;
  greetingCopy.textContent = `${activeLab.agents.length} AI researchers are here. Message everyone, @ one expert, or speak with the Lab Bot.`;
  resetLab();
}

function setLabState(agent = "director", state = "", detail = "") {
  const presence = presenceFor(agent);
  const nextState = state || presence.state;

  expertLabels.forEach((label) => {
    label.classList.remove("active");
    const small = label.querySelector("small");
    if (small) small.textContent = "Ready";
  });
  labMemberButtons.forEach((button) => {
    button.classList.remove("active");
    const small = button.querySelector("small");
    if (small) small.textContent = memberRoles.get(button.dataset.agent) || "Research expert";
  });

  const currentAgent = agentFor(agent);
  if (currentAgent && !["complete", "error", "idle"].includes(nextState)) {
    const label = expertLabels.find((item) => item.dataset.agent === currentAgent.id);
    const member = labMemberButtons.find((item) => item.dataset.agent === currentAgent.id);
    label?.classList.add("active");
    member?.classList.add("active");
    if (label?.querySelector("small")) label.querySelector("small").textContent = detail || presence.action;
    if (member?.querySelector("small")) member.querySelector("small").textContent = "Working now";
    activeExpert = currentAgent.id;
  } else {
    activeExpert = "";
  }

  currentLabState = nextState;
  labPresence.dataset.state = nextState;
  if (nextState === "complete") {
    labAgent.textContent = "Handoff ready";
    labAction.textContent = detail || "The expert panel returned its strongest result";
  } else if (nextState === "error") {
    labAgent.textContent = "Lab needs attention";
    labAction.textContent = detail || "The current shift could not continue";
  } else if (nextState === "listening") {
    labAgent.textContent = "Listening";
    labAction.textContent = detail || "The Lab Bot is listening to you";
  } else if (nextState === "thinking") {
    labAgent.textContent = "Thinking";
    labAction.textContent = detail || "The Lab Bot is finding the interesting thread";
  } else if (nextState === "speaking") {
    labAgent.textContent = "Speaking";
    labAction.textContent = detail || "The Lab Bot is answering";
  } else if (nextState === "idle") {
    labAgent.textContent = "Lab ready";
    labAction.textContent =
      detail || `${activeAgents().length} expert${activeAgents().length === 1 ? " is" : "s are"} standing by`;
  } else {
    labAgent.textContent = presence.name;
    labAction.textContent = detail || presence.action;
  }
  refreshWorkspaceState();
}

function resetLab() {
  activeExpert = "";
  labPresence.dataset.idleVariant = String(Math.floor(Math.random() * 4));
  setLabState(
    "director",
    "idle",
    `${activeAgents().length} expert${activeAgents().length === 1 ? " is" : "s are"} standing by`,
  );
}

function refreshWorkspaceState() {
  if (voiceActive) workspaceState.textContent = "Live voice connected";
  else if (working) workspaceState.textContent = "Research team working";
  else if (currentLabState === "complete") workspaceState.textContent = "Handoff ready";
  else if (backgroundResearch) workspaceState.textContent = "Google Cloud ready";
  else workspaceState.textContent = "Local workspace";
}

async function loadLabs(preferredId = "") {
  const response = await fetch("/api/labs");
  if (!response.ok) throw new Error(`Could not load labs (${response.status}).`);
  labs = await response.json();
  const stored = preferredId || localStorage.getItem(LAB_STORAGE_KEY);
  activeLab = labs.find((lab) => lab.id === stored) || labs[0] || null;
  if (activeLab) localStorage.setItem(LAB_STORAGE_KEY, activeLab.id);
  renderActiveLab();
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
  brief.placeholder = copy.placeholder;
  promptHint.textContent = copy.hint;
  send.setAttribute("aria-label", copy.send);
  conversationMode.textContent = copy.conversation;
  executionMode.textContent = voiceActive
    ? "Live Audio"
    : mode === "research"
      ? "Google Cloud"
      : "Live session";
  modelName.textContent = voiceActive ? liveModelName : textModelName;
  if (mode === "explain") updateExplainTarget(explainTarget);
  if (!hasConversation) workspaceName.textContent = copy.workspace;
  if (focus) brief.focus();
}

function closeSidebar() {
  document.body.classList.remove("sidebar-visible");
}

function setMembersVisible(visible) {
  document.body.classList.toggle("members-visible", visible);
  membersToggle.setAttribute("aria-expanded", String(visible));
}

function resizeComposer() {
  brief.style.height = "auto";
  brief.style.height = `${Math.min(brief.scrollHeight, 190)}px`;
}

function mentionContext() {
  const cursor = brief.selectionStart ?? brief.value.length;
  const beforeCursor = brief.value.slice(0, cursor);
  const match = beforeCursor.match(/(^|\s)@([^\s@]*)$/u);
  if (!match) return null;
  return {
    cursor,
    query: match[2].toLowerCase(),
    start: cursor - match[0].length + match[1].length,
  };
}

function updateMentionHighlight() {
  visibleMentionOptions.forEach((option, index) => {
    const active = index === mentionIndex;
    option.classList.toggle("mention-active", active);
    option.setAttribute("aria-selected", String(active));
  });
}

function closeMentionMenu() {
  mentionMenu.hidden = true;
  visibleMentionOptions = [];
  mentionIndex = 0;
}

function refreshMentionMenu() {
  const context = mentionContext();
  if (!context) {
    closeMentionMenu();
    return;
  }
  visibleMentionOptions = mentionOptions.filter((option) =>
    option.dataset.mention.toLowerCase().startsWith(context.query),
  );
  mentionOptions.forEach((option) => {
    option.hidden = !visibleMentionOptions.includes(option);
  });
  if (!visibleMentionOptions.length) {
    closeMentionMenu();
    return;
  }
  mentionIndex = Math.min(mentionIndex, visibleMentionOptions.length - 1);
  mentionMenu.hidden = false;
  updateMentionHighlight();
}

function selectMention(option) {
  const context = mentionContext();
  if (!context) return;
  brief.setRangeText(`@${option.dataset.mention} `, context.start, context.cursor, "end");
  closeMentionMenu();
  resizeComposer();
  brief.focus();
}

function insertMention(name) {
  const cursor = brief.selectionStart ?? brief.value.length;
  const prefix = cursor > 0 && !/\s$/.test(brief.value.slice(0, cursor)) ? " " : "";
  brief.setRangeText(`${prefix}@${name} `, cursor, cursor, "end");
  closeMentionMenu();
  resizeComposer();
  brief.focus();
}

function startNewResearch(nextMode = "research") {
  if (working) return;
  setMembersVisible(false);
  closeMentionMenu();
  hasConversation = false;
  activeSessionId = "";
  latestResearchOutput = "";
  streamedEntries.clear();
  renderedRunSequences.clear();
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
  conversationLabName.textContent = activeLab.name;
  workspaceName.textContent = activeLab.name;
  addEntry("You", raw, "human");
  brief.value = "";
  brief.style.height = "";
  window.scrollTo({ top: 0, behavior: "auto" });
}

function setWorking(nextWorking) {
  working = nextWorking;
  document.body.classList.toggle("working", working);
  form.setAttribute("aria-busy", String(working));
  send.disabled = working;
  brief.readOnly = working;
  refreshWorkspaceState();
}

function createEntry(author, kind) {
  const entry = document.createElement("article");
  entry.className = `message ${kind} message-in`;
  const content = document.createElement("div");
  content.className = "message-content";
  const label = document.createElement("div");
  label.className = "message-label";
  const authorAgent = agentFor(author);
  if (kind === "assistant") label.textContent = authorAgent?.name || "Research Director";
  else if (kind === "tool") label.textContent = authorAgent?.name || author;
  else label.textContent = author;
  const body = document.createElement("p");
  body.className = "message-body";
  content.append(label, body);
  if (kind === "assistant") {
    entry.append(
      avatarElement(authorAgent || { id: "everyone", color: "#111111" }),
      content,
    );
  } else {
    entry.append(content);
  }
  transcript.append(entry);
  return { entry, body };
}

function setEntryText(body, text) {
  body.replaceChildren();
  const pattern = /https?:\/\/[^\s<]+/gu;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    const index = match.index ?? 0;
    let url = match[0];
    let trailing = "";
    while (/[),.;:]$/u.test(url)) {
      trailing = url.at(-1) + trailing;
      url = url.slice(0, -1);
    }
    body.append(document.createTextNode(text.slice(cursor, index)));
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = url;
    body.append(link, document.createTextNode(trailing));
    cursor = index + match[0].length;
  }
  body.append(document.createTextNode(text.slice(cursor)));
}

function addEntry(author, text, kind = "assistant") {
  if (!text) return null;
  const result = createEntry(author, kind);
  setEntryText(result.body, text);
  result.entry.scrollIntoView({ behavior: "smooth", block: "end" });
  return result;
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
    setEntryText(streamed.body, text);
    streamedEntries.delete(key);
  }
  streamed.entry.scrollIntoView({ behavior: "smooth", block: "end" });
}

function eventText(event) {
  return (event.content?.parts || [])
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
  const functionName = (event.content?.parts || []).find((part) => part.functionCall?.name)
    ?.functionCall?.name;
  const presence = presenceFor(functionName || author);
  setLabState(presence.id, presence.state, presence.action);
  const isTool = text.startsWith("Calling ") || text.startsWith("Evidence returned");
  upsertStreamedEntry(event, author, text, isTool ? "tool" : "assistant");
}

async function runResearch(prompt) {
  activeSessionId ||= crypto.randomUUID();
  const request = await fetch(`/api/labs/${encodeURIComponent(activeLab.id)}/run_sse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, session_id: activeSessionId, user_id: USER_ID }),
  });
  if (!request.ok || !request.body) {
    const result = await request.json().catch(() => ({}));
    throw new Error(result.detail || `The research service returned ${request.status}.`);
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

function saveActiveRun(run) {
  localStorage.setItem(ACTIVE_RUN_KEY, JSON.stringify(run));
}

function readActiveRun() {
  try {
    const run = JSON.parse(localStorage.getItem(ACTIVE_RUN_KEY) || "null");
    if (!run?.run_id || !run?.lab_id || !run?.brief) return null;
    return run;
  } catch {
    localStorage.removeItem(ACTIVE_RUN_KEY);
    return null;
  }
}

function clearActiveRun(runId) {
  if (readActiveRun()?.run_id === runId) localStorage.removeItem(ACTIVE_RUN_KEY);
}

function rememberHandoff(text) {
  latestResearchOutput = text;
  if (text) localStorage.setItem(LAST_HANDOFF_KEY, text);
}

function renderBackgroundEvent(event) {
  if (renderedRunSequences.has(event.sequence)) return;
  renderedRunSequences.add(event.sequence);
  const detail = event.detail || "Research moved forward";
  setLabState(event.agent || "director", event.state || "working", detail);
  if (event.output) {
    rememberHandoff(event.output);
    addEntry(
      event.agent || "Research Director",
      event.output,
      event.state === "error" ? "error" : "assistant",
    );
  } else {
    addEntry(event.agent || "Research Director", detail, "tool");
  }
}

function waitForNextPoll() {
  return new Promise((resolve) => window.setTimeout(resolve, RUN_POLL_INTERVAL));
}

async function followBackgroundRun(runId) {
  while (true) {
    const response = await fetch(`/api/runs/${encodeURIComponent(runId)}`, {
      headers: { Accept: "application/json" },
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(
        result.detail || "The run is still in Google Cloud, but its activity could not be read.",
      );
    }
    (result.events || []).forEach(renderBackgroundEvent);
    if (result.done) {
      clearActiveRun(runId);
      return;
    }
    await waitForNextPoll();
  }
}

async function dispatchBackgroundResearch(prompt, raw) {
  const response = await fetch("/api/dispatch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief: prompt, lab_id: activeLab.id }),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(result.detail || `Google Cloud returned ${response.status}.`);
  }
  const run = {
    run_id: result.run_id,
    lab_id: activeLab.id,
    lab_name: activeLab.name,
    brief: raw,
    started_at: new Date().toISOString(),
  };
  saveActiveRun(run);
  addEntry("Google Cloud", `Run ${result.run_id.slice(0, 8)} started. You can leave this page.`, "tool");
  await followBackgroundRun(result.run_id);
}

async function restoreBackgroundRun(run) {
  if (!run) return false;
  const lab = labs.find((item) => item.id === run.lab_id);
  if (!lab) {
    localStorage.removeItem(ACTIVE_RUN_KEY);
    return false;
  }
  activeLab = lab;
  localStorage.setItem(LAB_STORAGE_KEY, lab.id);
  renderActiveLab();
  setMode("research");
  openConversation(run.brief);
  renderedRunSequences.clear();
  addEntry("Google Cloud", `Rejoined run ${run.run_id.slice(0, 8)}. Reading its real activity.`, "tool");
  setWorking(true);
  setLabState("director", "directing", "Rejoining the expert panel in Google Cloud");
  try {
    await followBackgroundRun(run.run_id);
    setLabState("director", "complete", "The evidence-backed handoff is ready");
  } catch (error) {
    setLabState("director", "error", "The run continues, but its activity is not visible yet");
    addEntry("Service", error.message || String(error), "error");
  } finally {
    setWorking(false);
  }
  return true;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function buildPrompt(raw) {
  const named = activeAgents()
    .filter((agent) => new RegExp(`@${escapeRegExp(agent.name)}\\b`, "iu").test(raw))
    .map((agent) => agent.name);
  if (/@Everyone\b/iu.test(raw)) {
    return `The human PI addressed the whole ${activeLab.name}. Recruit only the useful experts and let each speak in their own voice.\n\n${raw}`;
  }
  if (named.length) {
    return `The human PI addressed ${named.join(", ")} directly. Let them answer first. Invite another expert only if it makes the work stronger.\n\n${raw}`;
  }
  if (mode === "research") {
    return `Take over this research program for ${activeLab.name}. Return the strongest evidence-backed handoff.\n\n${raw}`;
  }
  const prior =
    explainTarget === "research" && latestResearchOutput
      ? `\n\nCurrent research handoff:\n${latestResearchOutput}`
      : "";
  return `${explainPrompts[explainTarget]}\n\n${raw}${prior}`;
}

function slugAgent(name, fallback) {
  let slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  if (!/^[a-z]/.test(slug)) slug = `researcher_${fallback}`;
  return slug.slice(0, 48);
}

function agentEditorRow(agent, index) {
  const row = document.createElement("div");
  row.className = "agent-editor-row";
  row.dataset.agentId = agent.id || "";
  const number = document.createElement("span");
  number.className = "agent-number";
  number.textContent = String(index + 1).padStart(2, "0");
  const color = document.createElement("input");
  color.className = "agent-color";
  color.type = "color";
  color.value = agent.color;
  color.setAttribute("aria-label", `Color for researcher ${index + 1}`);
  const fields = document.createElement("div");
  fields.className = "agent-row-fields";
  const name = document.createElement("input");
  name.className = "agent-name";
  name.required = true;
  name.maxLength = 48;
  name.placeholder = "Researcher name";
  name.value = agent.name;
  const role = document.createElement("textarea");
  role.className = "agent-role";
  role.required = true;
  role.maxLength = 400;
  role.rows = 2;
  role.placeholder = "One clear research responsibility";
  role.value = agent.role;
  fields.append(name, role);
  const remove = document.createElement("button");
  remove.className = "remove-agent";
  remove.type = "button";
  remove.dataset.removeAgent = String(index);
  remove.textContent = "×";
  remove.setAttribute("aria-label", `Remove researcher ${index + 1}`);
  row.append(number, color, fields, remove);
  return row;
}

function renderAgentEditor() {
  agentEditorList.replaceChildren();
  editorAgents.forEach((agent, index) => agentEditorList.append(agentEditorRow(agent, index)));
  $("#add-agent").disabled = editorAgents.length >= 12;
}

function openLabEditor(lab = null) {
  editingLabId = lab?.id || "";
  labDialogTitle.textContent = lab ? "Edit lab" : "Create a lab";
  labNameInput.value = lab?.name || "New Research Lab";
  labMissionInput.value =
    lab?.mission || "Find one important, testable research opening and make it undeniable.";
  editorAgents = structuredClone(
    lab?.agents || [
      { id: "scout", name: "Scout", role: "Search live papers, code, and overlooked tasks.", color: "#ff5eb1" },
      { id: "scientist", name: "Scientist", role: "Develop the mechanism and design the decisive experiment.", color: "#a97efe" },
      { id: "critic", name: "Critic", role: "Try to falsify the strongest claim before compute is spent.", color: "#111111" },
      { id: "explainer", name: "Explainer", role: "Make the evidence, uncertainty, and next move clear to the PI.", color: "#2a92fe" },
    ],
  );
  labEditorError.textContent = "";
  deleteLabButton.hidden = !lab;
  renderAgentEditor();
  labDialog.showModal();
  requestAnimationFrame(() => labNameInput.focus());
}

function syncEditorAgents() {
  editorAgents = [...agentEditorList.querySelectorAll(".agent-editor-row")].map((row, index) => ({
    id: row.dataset.agentId || "",
    name: row.querySelector(".agent-name").value.trim(),
    role: row.querySelector(".agent-role").value.trim(),
    color: row.querySelector(".agent-color").value,
    index,
  }));
}

function editorPayload() {
  syncEditorAgents();
  const used = new Set();
  const agents = editorAgents.map((agent, index) => {
    let id = agent.id || slugAgent(agent.name, index + 1);
    while (used.has(id)) id = `${id}_${index + 1}`.slice(0, 48);
    used.add(id);
    return { id, name: agent.name, role: agent.role, color: agent.color };
  });
  return { name: labNameInput.value.trim(), mission: labMissionInput.value.trim(), agents };
}

function formatApiError(result, fallback) {
  if (typeof result.detail === "string") return result.detail;
  if (Array.isArray(result.detail)) return result.detail.map((item) => item.msg).join(" · ");
  return fallback;
}

async function saveLab(event) {
  event.preventDefault();
  if (!editorAgents.length) {
    labEditorError.textContent = "A lab needs at least one researcher.";
    return;
  }
  const payload = editorPayload();
  const endpoint = editingLabId ? `/api/labs/${editingLabId}` : "/api/labs";
  const response = await fetch(endpoint, {
    method: editingLabId ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    labEditorError.textContent = formatApiError(result, `Could not save the lab (${response.status}).`);
    return;
  }
  labDialog.close();
  await stopVoice();
  await loadLabs(result.id);
  startNewResearch(mode);
}

async function deleteCurrentLab() {
  if (!editingLabId) return;
  if (!window.confirm("Delete this lab? Its definition will be removed from this demo.")) return;
  const response = await fetch(`/api/labs/${editingLabId}`, { method: "DELETE" });
  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    labEditorError.textContent = formatApiError(result, `Could not delete the lab (${response.status}).`);
    return;
  }
  labDialog.close();
  await stopVoice();
  await loadLabs();
  startNewResearch(mode);
}

function stopVoicePlayback() {
  voiceSources.forEach((source) => {
    try {
      source.stop();
    } catch {
      // The source may already have ended.
    }
  });
  voiceSources.clear();
  voiceOutputAt = 0;
}

async function playVoiceAudio(buffer) {
  voiceOutputContext ||= new AudioContext({ sampleRate: 24000 });
  if (voiceOutputContext.state === "suspended") await voiceOutputContext.resume();
  const pcm = new Int16Array(buffer);
  const samples = new Float32Array(pcm.length);
  let energy = 0;
  for (let index = 0; index < pcm.length; index += 1) {
    samples[index] = pcm[index] / 32768;
    energy += samples[index] * samples[index];
  }
  const level = Math.min(1, Math.sqrt(energy / Math.max(1, samples.length)) * 4.5);
  labPresence.style.setProperty("--voice-level", level.toFixed(3));
  setLabState("director", "speaking", "The Lab Bot is answering");
  const audio = voiceOutputContext.createBuffer(1, samples.length, 24000);
  audio.copyToChannel(samples, 0);
  const source = voiceOutputContext.createBufferSource();
  source.buffer = audio;
  source.connect(voiceOutputContext.destination);
  const startAt = Math.max(voiceOutputContext.currentTime + 0.025, voiceOutputAt);
  voiceOutputAt = startAt + audio.duration;
  voiceSources.add(source);
  source.onended = () => {
    voiceSources.delete(source);
    if (!voiceSources.size && voiceActive) {
      labPresence.style.setProperty("--voice-level", "0");
      setLabState("director", "listening", "I'm listening");
    }
  };
  source.start(startAt);
}

function updateVoiceTranscript(kind, text, final) {
  if (!text) return;
  if (!hasConversation) {
    labAction.textContent = text.length > 104 ? `${text.slice(0, 101)}…` : text;
    return;
  }
  if (kind === "human") {
    voiceUserEntry ||= createEntry("You", "human");
    voiceUserEntry.body.textContent = text;
    if (final) voiceUserEntry = null;
  } else {
    voiceBotEntry ||= createEntry("Research Director", "assistant");
    voiceBotEntry.body.textContent += text;
    if (final) voiceBotEntry = null;
  }
}

function handleVoiceLevel(level) {
  if (!voiceActive || voiceSources.size) return;
  if (level > 0.025) {
    voiceHeardSpeech = true;
    window.clearTimeout(voiceSilenceTimer);
    setLabState("director", "listening", "I'm listening");
    voiceSilenceTimer = window.setTimeout(() => {
      if (voiceActive && voiceHeardSpeech && !voiceSources.size) {
        setLabState("director", "thinking", "Finding the interesting thread");
      }
    }, 680);
  }
}

function handleVoiceMessage(event) {
  if (event.data instanceof Blob) {
    event.data.arrayBuffer().then(playVoiceAudio);
    return;
  }
  const message = JSON.parse(event.data);
  if (message.type === "ready") {
    voiceToggle.disabled = false;
    setLabState("director", "listening", "I'm listening");
  } else if (message.type === "input_transcript") {
    updateVoiceTranscript("human", message.text, message.final);
    if (message.final) setLabState("director", "thinking", "Finding the interesting thread");
  } else if (message.type === "output_transcript" || message.type === "output_text") {
    updateVoiceTranscript("assistant", message.text, message.final);
  } else if (message.type === "interrupted") {
    stopVoicePlayback();
    setLabState("director", "listening", "I'm listening");
  } else if (message.type === "turn_complete") {
    voiceUserEntry = null;
    voiceBotEntry = null;
  } else if (message.type === "error") {
    stopVoice(message.message || "Live Audio could not connect.");
  }
}

async function startVoice() {
  if (voiceActive || !activeLab) return;
  if (!navigator.mediaDevices?.getUserMedia || !window.AudioContext || !window.AudioWorkletNode) {
    setLabState("director", "error", "This browser does not support realtime audio");
    return;
  }
  voiceToggle.disabled = true;
  voiceToggle.setAttribute("aria-pressed", "true");
  executionMode.textContent = "Live Audio";
  modelName.textContent = liveModelName;
  document.body.classList.add("voice-active");
  setLabState("director", "thinking", "Opening a private Live Audio session");
  try {
    voiceStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    voiceInputContext = new AudioContext();
    await voiceInputContext.audioWorklet.addModule("/static/pcm-processor.js");
    const source = voiceInputContext.createMediaStreamSource(voiceStream);
    voiceProcessor = new AudioWorkletNode(voiceInputContext, "cloud-research-pcm");
    const silent = voiceInputContext.createGain();
    silent.gain.value = 0;
    source.connect(voiceProcessor);
    voiceProcessor.connect(silent).connect(voiceInputContext.destination);

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    voiceSocket = new WebSocket(
      `${protocol}://${window.location.host}/api/labs/${encodeURIComponent(activeLab.id)}/live`,
    );
    voiceSocket.binaryType = "arraybuffer";
    voiceSocket.onopen = () => {
      voiceSocket.send(
        JSON.stringify({
          type: "start",
          handoff: latestResearchOutput || localStorage.getItem(LAST_HANDOFF_KEY) || "",
        }),
      );
    };
    voiceProcessor.port.onmessage = ({ data }) => {
      handleVoiceLevel(data.level || 0);
      if (voiceSocket?.readyState === WebSocket.OPEN) voiceSocket.send(data.pcm);
    };
    voiceSocket.onmessage = handleVoiceMessage;
    voiceSocket.onerror = () => stopVoice("Live Audio connection failed");
    voiceSocket.onclose = () => {
      if (voiceActive) stopVoice("Live Audio disconnected");
    };
    voiceActive = true;
    refreshWorkspaceState();
  } catch (error) {
    await stopVoice(error.message || "Microphone access was not available");
  }
}

async function stopVoice(message = "") {
  if (
    !voiceActive &&
    !voiceSocket &&
    !voiceStream &&
    voiceToggle.getAttribute("aria-pressed") !== "true"
  ) {
    return;
  }
  voiceActive = false;
  voiceHeardSpeech = false;
  window.clearTimeout(voiceSilenceTimer);
  document.body.classList.remove("voice-active");
  voiceToggle.disabled = false;
  voiceToggle.setAttribute("aria-pressed", "false");
  executionMode.textContent = mode === "research" ? "Google Cloud" : "Live session";
  modelName.textContent = textModelName;
  stopVoicePlayback();
  voiceProcessor?.disconnect();
  voiceProcessor = null;
  voiceStream?.getTracks().forEach((track) => track.stop());
  voiceStream = null;
  if (voiceSocket && voiceSocket.readyState < WebSocket.CLOSING) voiceSocket.close(1000);
  voiceSocket = null;
  if (voiceInputContext && voiceInputContext.state !== "closed") await voiceInputContext.close();
  voiceInputContext = null;
  voiceUserEntry = null;
  voiceBotEntry = null;
  if (message) setLabState("director", "error", message);
  else resetLab();
  refreshWorkspaceState();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const raw = brief.value.trim();
  if (!raw || working || !activeLab) return;
  if (!hasConversation) openConversation(raw);
  else {
    addEntry("You", raw, "human");
    brief.value = "";
    brief.style.height = "";
  }
  setWorking(true);
  setLabState("director", "directing", "The Director is reading the research brief");
  try {
    const prompt = buildPrompt(raw);
    if (mode === "research" && backgroundResearch) {
      await dispatchBackgroundResearch(prompt, raw);
    } else {
      await runResearch(prompt);
    }
    rememberHandoff(
      [...transcript.querySelectorAll(".message.assistant .message-body")]
        .map((node) => node.textContent)
        .join("\n\n"),
    );
    setLabState(
      mode === "explain" ? "explainer" : "director",
      "complete",
      mode === "explain" ? "The explanation is ready" : "The evidence-backed handoff is ready",
    );
  } catch (error) {
    setLabState("director", "error", "The current shift could not continue");
    addEntry("Service", error.message || String(error), "error");
  } finally {
    setWorking(false);
    brief.focus();
  }
});

$("#sidebar-open").addEventListener("click", () => document.body.classList.add("sidebar-visible"));
$("#sidebar-close").addEventListener("click", closeSidebar);
$("#sidebar-scrim").addEventListener("click", closeSidebar);
membersToggle.addEventListener("click", () =>
  setMembersVisible(!document.body.classList.contains("members-visible")),
);
membersClose.addEventListener("click", () => setMembersVisible(false));
membersScrim.addEventListener("click", () => setMembersVisible(false));

modeButtons.forEach((button) =>
  button.addEventListener("click", () => setMode(button.dataset.mode, true)),
);
navModeButtons.forEach((button) =>
  button.addEventListener("click", () => {
    startNewResearch(button.dataset.navMode);
    closeSidebar();
  }),
);
explainTargetButtons.forEach((button) =>
  button.addEventListener("click", () => {
    updateExplainTarget(button.dataset.explainTarget);
    brief.focus();
  }),
);
suggestionButtons.forEach((button) =>
  button.addEventListener("click", () => {
    setMode(button.dataset.suggestionMode);
    brief.value = button.dataset.suggestion;
    resizeComposer();
    brief.focus();
  }),
);

$("#new-research").addEventListener("click", () => {
  startNewResearch("research");
  closeSidebar();
});
newLabButton.addEventListener("click", () => openLabEditor());
manageLabButton.addEventListener("click", () => activeLab && openLabEditor(activeLab));
$("#lab-dialog-close").addEventListener("click", () => labDialog.close());
$("#cancel-lab").addEventListener("click", () => labDialog.close());
$("#add-agent").addEventListener("click", () => {
  syncEditorAgents();
  if (editorAgents.length >= 12) return;
  const index = editorAgents.length;
  editorAgents.push({
    id: "",
    name: `Researcher ${index + 1}`,
    role: "Own one clear part of the research mission.",
    color: DEFAULT_AGENT_COLORS[index % DEFAULT_AGENT_COLORS.length],
  });
  renderAgentEditor();
  agentEditorList.lastElementChild?.querySelector(".agent-name")?.focus();
});
agentEditorList.addEventListener("click", (event) => {
  const remove = event.target.closest("[data-remove-agent]");
  if (!remove) return;
  syncEditorAgents();
  if (editorAgents.length === 1) {
    labEditorError.textContent = "A lab needs at least one researcher.";
    return;
  }
  editorAgents.splice(Number(remove.dataset.removeAgent), 1);
  renderAgentEditor();
});
labEditor.addEventListener("submit", saveLab);
deleteLabButton.addEventListener("click", deleteCurrentLab);

labList.addEventListener("click", async (event) => {
  const switcher = event.target.closest("[data-lab-id]");
  if (!switcher || working || switcher.dataset.labId === activeLab?.id) return;
  await stopVoice();
  activeLab = labs.find((lab) => lab.id === switcher.dataset.labId);
  localStorage.setItem(LAB_STORAGE_KEY, activeLab.id);
  renderActiveLab();
  startNewResearch(mode);
  closeSidebar();
});

function handleAssignmentClick(event) {
  const button = event.target.closest("[data-mention]");
  if (!button) return;
  if (button.closest("#mention-menu")) selectMention(button);
  else insertMention(button.dataset.mention);
  setMembersVisible(false);
}

mentionMenu.addEventListener("click", handleAssignmentClick);
teamList.addEventListener("click", handleAssignmentClick);
memberList.addEventListener("click", handleAssignmentClick);
mentionTrigger.addEventListener("click", () => {
  const cursor = brief.selectionStart ?? brief.value.length;
  const prefix = cursor > 0 && !/\s$/.test(brief.value.slice(0, cursor)) ? " " : "";
  brief.setRangeText(`${prefix}@`, cursor, cursor, "end");
  brief.focus();
  refreshMentionMenu();
});

brief.addEventListener("input", () => {
  resizeComposer();
  refreshMentionMenu();
});
brief.addEventListener("keydown", (event) => {
  if (!mentionMenu.hidden) {
    if ((event.key === "ArrowDown" || event.key === "ArrowUp") && visibleMentionOptions.length) {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      mentionIndex =
        (mentionIndex + direction + visibleMentionOptions.length) % visibleMentionOptions.length;
      updateMentionHighlight();
      return;
    }
    if ((event.key === "Enter" || event.key === "Tab") && visibleMentionOptions.length) {
      event.preventDefault();
      selectMention(visibleMentionOptions[mentionIndex]);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      closeMentionMenu();
      return;
    }
  }
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (brief.value.trim() && !working) form.requestSubmit();
  }
});

document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest("#research-form")) closeMentionMenu();
});
voiceToggle.addEventListener("click", () => (voiceActive ? stopVoice() : startVoice()));
labBot.addEventListener("click", () => (voiceActive ? stopVoice() : startVoice()));

async function initialize() {
  setMode("research");
  try {
    const [about] = await Promise.all([
      fetch("/api/about").then((response) => response.json()),
      loadLabs(),
    ]);
    backgroundResearch = Boolean(about.background_research);
    textModelName = about.model || textModelName;
    liveModelName = about.live_model || liveModelName;
    modelName.textContent = textModelName;
    executionMode.textContent = "Google Cloud";
    const restored = backgroundResearch && (await restoreBackgroundRun(readActiveRun()));
    if (!restored) resetLab();
  } catch (error) {
    workspaceState.textContent = "Setup needs attention";
    labAction.textContent = error.message || "The lab could not start";
    labPresence.dataset.state = "error";
  }
}

initialize();
