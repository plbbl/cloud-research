# Cloud Research modules

Cloud Research was built from scratch during the hackathon submission period. It is a thin,
prompt-directed research lab, not a wrapper around an earlier application runtime. The human PI
sets the question, boundary, and compute budget; Gemini experts decide which useful move comes next.

| Module | Responsibility | Google / cloud surface |
| --- | --- | --- |
| Director | Reads the brief and recruits useful experts in any order. | Google ADK `Agent` + `AgentTool`; Gemini 3.7 Flash on Vertex AI |
| Finder | Maps live papers, code, and the nearest research opening. | Google Search grounding |
| Theorist | Sharpens mechanisms, predictions, proofs, and counterexamples. | Gemini reasoning + claim comparison tool |
| Experimentalist | Runs the cheapest decisive probe available. | ADK built-in code execution |
| Critic | Attacks novelty, evidence, mechanism, and the obvious alternative. | Gemini adversarial review |
| Writer | Preserves evidence, failures, unknowns, and the next task. | Artifact tool + optional GitHub branch |
| Explainer | Rebuilds a task, paper, result, or handoff in plain language. | Gemini response in chat or Live debrief |
| Research Job | Keeps one prompt-led shift alive after the browser closes. | Cloud Run Jobs |
| Fact ledger | Stores append-only labs, events, delivery claims, and handoffs. | Cloud Firestore |
| Event gateway | Verifies a signed GitHub event and launches the selected Job. | Cloud Run + Secret Manager + HMAC |
| Lab UI | Lets a human create labs, edit roles, @mention experts, and rejoin a run. | Cloud Run web service + Firestore |
| Live debrief | Lets the PI question the finished research aloud. | Gemini Live native audio |

## The deliberate deletion

The scientific path is not encoded as a custom state machine. Short prompts carry the research
taste and evidence labels; ADK lets the Director choose the next expert, and Cloud Run owns only
process lifetime and retry policy. Firestore stores facts, not scientific routing decisions.
