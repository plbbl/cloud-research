# Existing system → Cloud Research

The original system at `/Users/a1234/Desktop/auto research` remains read-only. This project does
not import its runtime, databases, runs, secrets, watchdogs, queues, or GPU launchers.

| Existing capability | Cloud Research version | Why |
| --- | --- | --- |
| Find-task prompts and discovery operators | `finder` | Preserves the taste for mechanism cracks, nearest work, and cheap falsifiers. Google Search supplies live evidence. |
| Topic pusher / critic / chief | `theorist` + `critic` + model-led Director | Preserves optimistic adversarial research without encoding a committee workflow. |
| CPU/GPU experiment workers | `experimentalist` | Uses Gemini built-in isolated Python execution for cheap probes. Expensive local GPU work remains a handoff. |
| Candidate overlap helpers | `research_logic.py` | Ports only deterministic lexical helpers; Gemini still judges mechanism-level novelty. |
| Manuscript and report writers | `writer` | Produces an evidence-backed packet and can publish it to a GitHub branch. |
| Human-facing explainer | `explainer` | Makes a research run or paper genuinely understandable, not merely shorter. |
| Local dashboard | Cloud Run web surface | One prompt starts the team; ADK streams the public research notebook. |

## The deliberate deletion

The old system needs many states because it coordinates local processes. The hackathon version
does not imitate that machinery. One ADK Director can recruit any expert, any number of times, in
whatever order the evidence demands. Cloud Run owns the process lifetime; GitHub or a Markdown
artifact owns the handoff. There is no scientific state machine between them.

