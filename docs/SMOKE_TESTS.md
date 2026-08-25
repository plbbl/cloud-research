# Real smoke tests

Date: 2026-08-25  
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

## Automated checks after live-event work

- 20 Python tests passed.
- JavaScript syntax check passed.
- Ruff passed.
- Structured event tests cover agent-to-expression mapping, safe UUID filters, Cloud Logging order,
  Cloud Run Job overrides, and the run-status API.
