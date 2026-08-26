# Real smoke tests

Date: 2026-08-26
Project: `x-cycling-506610-p8`
Model: `gemini-3.7-flash`

These are deliberately small integration tests, not research-quality evaluations.

## Private service: Director to Explainer

Prompt: ask Explainer only to explain why one counterexample invalidates a universal claim in at
most 120 English words.

Observed:

- Private Cloud Run HTTPS session created successfully.
- ADK Director called only `explainer`.
- Explainer returned a correct formal and plain-language account.
- No search, code execution, Writer, or background Job was used.
- Observed model usage: 1,398 total tokens across the Director and delegated response.

## Background Job: code, explanation, and handoff

Execution: `cloud-research-shift-ggrxn`

Prompt: compute the sum of the first ten natural squares, explain what was verified, write a
three-line packet, use no search, then stop.

Observed:

- Cloud Run Job completed successfully in 2 minutes 13.79 seconds.
- One task succeeded, zero failed, zero retries.
- Experimentalist executed `sum(i*i for i in range(1, 11))` and returned `385`.
- The closed-form result also returned `385`.
- Explainer described the verification in two sentences.
- Writer produced a compact claim, evidence, and next-move packet.

## Signed GitHub event: no browser

Issue: https://github.com/plbbl/cloud-research/issues/1
Execution: `cloud-research-shift-6mnfr`
Run ID: `363dea89-6ece-4eeb-9f6c-7d49cad4f703`

Observed:

- GitHub delivered the `issues/labeled` event to the public gateway with HTTP 200.
- HMAC verification and Firestore delivery deduplication ran before dispatch.
- The Job completed successfully in 8 minutes 10.1 seconds: one task succeeded, zero failed.
- Eight real events named the custom Lab's Scout, Mechanist, Probe, Skeptic, Handoff, and Explainer.
- Writer published `cloud-research/confidence-based-tta-failure-under-mixed-shift`.
- The Issue comment explicitly marks the mechanism and thresholds as proposed pending the listed
  one-GPU falsification experiment.

After the gateway moved to its separate least-privilege identity, a new external GitHub ping again
returned HTTP 200 in 0.05 seconds.

## Native Live debrief

The first real bridge test exposed a region bug: the Live client inherited the text model's
`global` Vertex location and failed to find the native-audio model. The client now gives Live an
independent `us-central1` location while text research remains global.

The repeatable `scripts/smoke_live.py` test then connected through the authenticated Cloud Run
proxy, supplied a current Handoff, and asked for the observed/proposed boundary. Observed:

- model: `gemini-live-2.5-flash-native-audio`;
- 42 audio frames / 452,714 bytes;
- output transcript, generation complete, and turn complete events;
- transcript: “The lab observed a result on a synthetic probe, but the claim that same mechanism
  will improve CLIP on a real benchmark is still just a proposal.”

The generated record is `evals/live-smoke.json`.

## Cross-domain evaluation and source audit

- Three real Cloud Run Jobs completed in 347.6–429.9 seconds.
- Each emitted 7–8 expert events and preserved killed paths, unknowns, next task, artifact, and URLs.
- 23 of 24 unique source URLs resolved; one nonexistent GitHub repository remained visible in the
  audit instead of being silently removed.
- `evals/latest-results.json` measures observable completion; `evals/source-audit.json` measures
  URL transport only. Neither file claims scientific validation.

## Fixes discovered by testing

- SSE fragments now update one visible message instead of creating duplicate message rows.
- The final Job response is logged once instead of being printed twice by the process entrypoint.

## Lab presence and responsive UI

Browser checks after the Lab Bot and Explainer work:

- Desktop: 1440 x 900, zero horizontal overflow, the composer stayed inside the workspace.
- Mobile: 390 x 844, zero horizontal overflow, the complete hero and composer fit one viewport.
- The four Explain targets measured as four equal 80 px controls on mobile.
- The mobile sidebar opened to 260 px with a working scrim and no layout shift.
- Two idle animation samples 700 ms apart had different transforms, confirming real motion.

## Continuous-session diagnostic

Two Result Explainer prompts were submitted in one local conversation. The server received one ADK
session creation and two `/run_sse` calls, confirming that follow-up turns reuse the same session.
The local process intentionally had no Gemini key or application-default credentials, so both model
calls exercised the visible error state instead of consuming a model. Real Gemini behavior remains
covered by the private-service smoke test above.

## Automated checks after event, Firestore, and Live work

- 43 Python tests passed.
- JavaScript syntax check passed.
- Ruff passed.
- Structured event tests cover agent-to-expression mapping, safe UUID filters, Cloud Logging order,
  selected-Lab Cloud Run Job overrides, custom-role capability inference, browser-run restoration,
  and the run-status API. Public-gateway tests also prove the model, Lab, and manual dispatch routes
  are absent from the unauthenticated surface.

## Final contest-path verification

- A no-cost Job double exercised the production `/api/dispatch` and `/api/runs/{run_id}` contract.
- The interface showed the real run ID, normalized the active expert's name, rendered a clickable
  evidence link, and kept the complete Handoff above the fixed composer.
- Reloading during the unfinished run restored the same Lab, brief, run ID, and Finder activity
  without submitting a second Job.
- The deployed image built successfully from the repository Dockerfile and returned a healthy
  Gemini 3.7 Flash / Vertex AI / Google ADK / Cloud Run / Firestore stack.

## Group-lab interaction

- Desktop 1440 x 900 shows the research discussion, six-member panel, live Director sphere, and
  bottom composer without overlap.
- Narrow 500 x 844 keeps the complete lobby and composer inside the viewport; the member panel
  becomes a drawer below the desktop breakpoint.
- Typing `@` opens all seven routing choices; typing `@Cri` filters to Critic and inserts
  `@Critic`.
- Arrow Down and Enter select Finder without a mouse.
- A submitted `@Critic` message renders as a human-PI chat bubble and preserves the visible service
  error when local credentials are intentionally absent.
