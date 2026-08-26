# Judging map

This maps the official rubric to evidence a judge can inspect in under four minutes.

## Innovation & Operational Utility — 40%

**Friction:** an independent researcher's attention is serial. Search, novelty checks, cheap probes,
criticism, documentation, and handoff stop when the researcher leaves.

**Twist:** the human becomes PI of a persistent, user-defined expert panel. Cloud Research does not
wait in a chat window; an ordinary GitHub Issue label starts a complete background shift.

**Proof:** Issue #1 launched an eight-minute Cloud Run Job with no open browser, recruited six
custom experts, preserved killed directions and unknowns, and published a continuation branch.

## Architectural Discipline & Tech Stack — 30%

- Gemini 3.7 Flash through Vertex AI performs reasoning and grounded search.
- Google ADK gives the Director a set of isolated expert `AgentTool`s; their order is model-chosen.
- Cloud Run separates the private model surface, durable one-shot Job, and tiny public event gateway.
- Firestore is append-only fact/state storage; it never chooses the next scientific action.
- Secret Manager holds the webhook and GitHub tokens separately.
- HMAC verification and delivery deduplication protect the external trigger.
- The public gateway's identity has no Vertex role and no access to the publishing token.
- Gemini model calls retry with bounded exponential backoff; Cloud Run Jobs use no automatic retry
  to avoid duplicating a costly shift from one delivery.
- A custom Critic challenges research output; a deterministic transport audit exposed one failed
  citation. The failure is retained because reachability and scientific support are different.

## Demo & Production Readiness — 30%

- Public MIT-licensed repository, third-party Apache-2.0 attribution, architecture diagram,
  reproducible setup, and 43 tests.
- Real GitHub HTTP 200, Cloud Run execution, Firestore facts, custom-agent events, and GitHub packet.
- Three repeatable multi-domain Jobs plus generated JSON evidence.
- Real Gemini Live bridge with 42 native-audio frames and output transcription.
- Exact four-minute script and evidence map; the Proof of Action segment is designed to be unedited.

## Optional contributions

- Public build story: https://github.com/plbbl/cloud-research/releases/tag/v0.1.0
- Social copy with `#AllThingsAgenticHackathon`: `docs/PUBLIC_BUILD_POST.md`
- Additional Google AI model: `gemini-live-2.5-flash-native-audio`, with measured proof in
  `evals/live-smoke.json`.
