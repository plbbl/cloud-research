const form = document.querySelector("#research-form");
const brief = document.querySelector("#research-brief");
const launch = document.querySelector(".launch");
const launchLabel = launch.querySelector("span");
const hint = document.querySelector("#prompt-hint");
const intro = document.querySelector("#intro");
const transcript = document.querySelector("#transcript");
const notebook = document.querySelector("#notebook");
const pulse = document.querySelector("#pulse");
const modeButtons = [...document.querySelectorAll(".mode")];
const expertLabels = [...document.querySelectorAll(".experts span")];

let mode = "research";
let backgroundResearch = false;

fetch("/api/about")
  .then((response) => response.json())
  .then((about) => {
    backgroundResearch = Boolean(about.background_research);
    if (backgroundResearch) {
      hint.textContent = "Cloud Run keeps the team working after you close this page.";
    }
  })
  .catch(() => {});

const copy = {
  research: {
    label: "Start research",
    hint: "The Director chooses who works, in what order, and for how long.",
    placeholder:
      "Give the field, the question, what you already know, your compute, and what would make tomorrow useful…",
  },
  explain: {
    label: "Explain this",
    hint: "Explainer reconstructs the default, surprise, evidence, uncertainty, and next move.",
    placeholder: "Paste a paper, abstract, research report, result, or question you want to truly understand…",
  },
};

modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    mode = button.dataset.mode;
    modeButtons.forEach((item) => item.classList.toggle("active", item === button));
    launchLabel.textContent = copy[mode].label;
    hint.textContent = copy[mode].hint;
    brief.placeholder = copy[mode].placeholder;
  });
});

document.querySelector("#example").addEventListener("click", () => {
  modeButtons[0].click();
  brief.value =
    "I have one 24 GB GPU. Find a cheap, falsifiable research opening in small-model test-time adaptation. Search the closest work, challenge novelty, run any small Python counterexample that matters, and leave me a research handoff I can continue tomorrow.";
  brief.focus();
});

function setWorking(working) {
  launch.disabled = working;
  pulse.classList.toggle("working", working);
  pulse.setAttribute("aria-label", working ? "Lab working" : "Lab ready");
  pulse.lastChild.textContent = working ? " WORKING" : " READY";
}

function markAgent(author = "") {
  const normalized = author.toLowerCase();
  expertLabels.forEach((label) => {
    label.classList.toggle("active", normalized.includes(label.dataset.agent));
  });
}

function addEntry(author, text, kind = "text") {
  if (!text) return;
  intro.hidden = true;
  const entry = document.createElement("article");
  entry.className = `entry ${kind}`;
  const label = document.createElement("div");
  label.className = "agent-label";
  label.textContent = author.toUpperCase().replaceAll("_", " ");
  const body = document.createElement("p");
  body.textContent = text;
  entry.append(label, body);
  transcript.append(entry);
  notebook.scrollTop = notebook.scrollHeight;
}

function eventText(event) {
  const parts = event.content?.parts || [];
  return parts
    .map((part) => {
      if (part.text) return part.text;
      if (part.functionCall?.name) return `Calling ${part.functionCall.name}`;
      if (part.functionResponse?.name) return `Received evidence from ${part.functionResponse.name}`;
      return "";
    })
    .filter(Boolean)
    .join("\n");
}

async function runResearch(prompt) {
  const sessionId = crypto.randomUUID();
  const userId = "human-pi";
  const appName = "app";
  await fetch(`/apps/${appName}/users/${userId}/sessions/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  }).then((response) => {
    if (!response.ok) throw new Error(`Could not open the lab (${response.status}).`);
  });

  const request = await fetch("/run_sse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      appName,
      userId,
      sessionId,
      streaming: true,
      newMessage: {
        role: "user",
        parts: [{ text: prompt }],
      },
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
    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const event = JSON.parse(line.slice(5).trim());
      if (event.error) throw new Error(event.error);
      const author = event.author || "research director";
      markAgent(author);
      const text = eventText(event);
      const isTool = text.startsWith("Calling ") || text.startsWith("Received evidence");
      addEntry(author, text, isTool ? "tool" : "text");
    }
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
  addEntry("cloud run", result.message);
  addEntry("operation", result.operation, "tool");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const raw = brief.value.trim();
  if (!raw) return;
  transcript.replaceChildren();
  markAgent("research director");
  setWorking(true);
  addEntry("human PI", raw);
  const prompt =
    mode === "explain"
      ? `Ask Explainer to make this truly understood:\n\n${raw}`
      : `Take over this research program and return the strongest evidence-backed handoff:\n\n${raw}`;
  try {
    if (backgroundResearch && mode === "research") {
      await dispatchResearch(prompt);
    } else {
      await runResearch(prompt);
      addEntry("cloud research", "Handoff complete. The next move belongs to you.");
    }
  } catch (error) {
    addEntry("service", error.message || String(error), "error");
  } finally {
    markAgent("");
    setWorking(false);
  }
});
