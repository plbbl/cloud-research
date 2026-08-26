# Reproducible evaluation

The evaluation measures only visible outcomes. It does not ask another model to declare that the
research is good.

For each brief it records:

- whether the Cloud Run Job completed;
- wall-clock duration and the number of real research events;
- the number of source URLs in the final Handoff;
- whether the Handoff preserves killed paths, unknowns, a next task, and an artifact.

A second, deliberately narrower audit requests every unique source URL. It measures transport
reachability only; HTTP 200 does **not** prove that the paper supports the claim.

Run against the authenticated Cloud Run proxy:

```bash
python scripts/evaluate.py --base-url http://127.0.0.1:8092 --workers 2
```

To recompute metrics from already completed Jobs without spending again:

```bash
python scripts/evaluate.py --base-url http://127.0.0.1:8092 \
  --limit 3 --resume-manifest evals/run-manifest.json

python scripts/check_sources.py
```

The six cases in `evals/research_cases.json` span different ML areas but share one constraint: a
single 24 GB GPU. `evals/latest-results.json` is generated evidence. It is committed only after a
real run; no sample result is presented as measured data.

## Measured contest run — 2026-08-26

Three real Cloud Run Jobs completed across vision-language adaptation, KV-cache failure analysis,
and synthetic-data contamination. All three returned killed paths, unknowns, a next task, an
artifact, and multiple source URLs. Durations were 347.6–429.9 seconds and the Jobs emitted 7–8
real expert events each.

The transport audit reached 23 of 24 unique URLs. It caught one nonexistent GitHub repository in
the vision-language Handoff, so only two of three cases passed the stricter “all links resolve”
check. That failure is kept in `evals/source-audit.json`; it is more useful than a perfect-looking
score because it identifies the exact evidence-integrity behavior the PI should challenge.
