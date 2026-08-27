# Demo evidence map

Use this page while recording. It separates public proof, owner-only console proof, and claims that
must remain qualified.

## Public proof

- Repository: https://github.com/plbbl/cloud-research
- Trigger and completion comment: https://github.com/plbbl/cloud-research/issues/1
- Event-generated packet: https://github.com/plbbl/cloud-research/blob/cloud-research/confidence-based-tta-failure-under-mixed-shift/research/confidence-tta-mixed-shift.md
- Architecture: `docs/cloud-research-architecture.drawio.svg`
- Reproducible evaluation: `evals/latest-results.json`
- Source transport audit: `evals/source-audit.json`
- Live result: `evals/live-smoke.json`

## Owner-only proof to show in the video

- GitHub webhook delivery `3839105655942152000`: Issues, HTTP 200, 0.67 seconds.
- Final-image ping `3839111268172570600`: HTTP 200, 0.06 seconds.
- Cloud Run Job execution: `cloud-research-shift-6mnfr`.
- Run ID: `363dea89-6ece-4eeb-9f6c-7d49cad4f703`.
- Job result: completed in 8 minutes 10.1 seconds; one succeeded, zero failed.
- Clean public proof Job: `cloud-research-proof`, with five consecutive executions
  (`hsqz6`, `z44xp`, `wmz4p`, `prpmg`, `9rshz`) all showing `1/1 completed` and exit code `0`.
- Private product revision: `cloud-research-00013-8qc`.
- Public event revision: `cloud-research-events-00004-9nm`.
- Shared final image digest: `sha256:87ea00a630ecb7b6fc1d2347f0ebe1bdf9ae3914ff92bea3009da30591b0c02c`.
- Firestore: `(default)`, Native mode, `us-central1`, `freeTier: true`, PITR disabled.

## Exact claims safe to say

- A signed GitHub label launched a custom Gemini/ADK research Lab without an open browser.
- The dedicated Cloud Run proof Job has five consecutive successful executions; this is the history
  shown in the submission video, while the continuous detail capture supplies the live Proof of
  Action.
- The run emitted eight real events across six user-defined experts and published a branch.
- Three cross-domain Jobs completed; 23 of 24 unique cited URLs resolved.
- Gemini Live returned 42 audio frames and a transcript grounded in the supplied Handoff.
- The model surface is private; the public gateway has no Vertex role or GitHub publishing token.

## Claims not safe to say

- The generated TTA mechanism has been validated on CLIP or ImageNet.
- A toy or synthetic probe proves a real-benchmark result.
- URL reachability proves that a source supports the generated claim.
- Cloud Research autonomously produces publication-ready science without PI review.
