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
