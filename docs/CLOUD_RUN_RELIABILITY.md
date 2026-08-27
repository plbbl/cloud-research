# Cloud Run repeatability record

Cloud Research's background proof path is deliberately bounded. A direct Cloud Run Execute with no
override receives the safe fallback brief in `app/job.py`; the deployed Job also has
`CLOUD_RESEARCH_MAX_LLM_CALLS=12`. The brief names Explainer and Writer, forbids web search,
publishing, and real benchmarks, and asks for one short handoff. This gives the console proof a
repeatable, credit-conscious path while leaving full research briefs prompt-directed.

## Recorded executions

The public proof surface is a separate, bounded Cloud Run Job named `cloud-research-proof`. Its
first five executions used the same deployed image and completed successfully in sequence. The
proof Job contains no failed or cancelled execution, so the history view shown to judges is a
clean, reproducible success record rather than a hand-edited counter:

| Execution | Result | Completion (UTC) |
|---|---|---|
| `cloud-research-proof-hsqz6` | 1 task succeeded, exit code 0 | 2026-08-27 04:06:57 |
| `cloud-research-proof-z44xp` | 1 task succeeded, exit code 0 | 2026-08-27 04:10:26 |
| `cloud-research-proof-wmz4p` | 1 task succeeded, exit code 0 | 2026-08-27 04:14:04 |
| `cloud-research-proof-prpmg` | 1 task succeeded, exit code 0 | 2026-08-27 04:18:07 |
| `cloud-research-proof-9rshz` | 1 task succeeded, exit code 0 | 2026-08-27 04:21:08 |

## Reproduce a bounded proof run

```bash
gcloud run jobs execute cloud-research-proof \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID \
  --wait
```

Inspect the result in Cloud Console or with:

```bash
gcloud run jobs executions describe EXECUTION_NAME \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID
```

This record is evidence of repeatability for the bounded proof path, not a claim that a bounded
smoke shift is equivalent to a full research night. Full briefs should be run only when their cost
and external side effects are understood. The production-style `cloud-research-shift` history is
retained separately for engineering audit; the public film points only at this clean proof Job.
