# Google Cloud setup

Project: `Cloud Research`  
Project ID: `x-cycling-506610-p8`  
Model: `gemini-3.7-flash`
Live Audio model: `gemini-live-2.5-flash-native-audio`

Cloud Research uses exactly the three competition layers:

1. **Gemini API through Vertex AI** for reasoning, Google Search grounding, and built-in code execution.
2. **Google ADK** for the Director and six model-selected expert agents.
3. **Cloud Run** for the HTTPS surface plus a durable one-shot Job that survives the browser.
4. **Cloud Firestore** as an append-only fact ledger for Labs, events, delivery deduplication, and
   Handoffs. It stores facts; it never routes science.

## APIs

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  logging.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  --project=x-cycling-506610-p8
```

## Service identity

```bash
gcloud iam service-accounts create cloud-research-run \
  --display-name="Cloud Research on Cloud Run" \
  --project=x-cycling-506610-p8

gcloud projects add-iam-policy-binding x-cycling-506610-p8 \
  --member="serviceAccount:cloud-research-run@x-cycling-506610-p8.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# The private service reads only this project's structured research-shift events.
gcloud projects add-iam-policy-binding x-cycling-506610-p8 \
  --member="serviceAccount:cloud-research-run@x-cycling-506610-p8.iam.gserviceaccount.com" \
  --role="roles/logging.viewer"

gcloud projects add-iam-policy-binding x-cycling-506610-p8 \
  --member="serviceAccount:cloud-research-run@x-cycling-506610-p8.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

The real project uses the Firestore Native `(default)` database in `us-central1`. Google reports
`freeTier: true`; point-in-time recovery, backups, and TTL policies are disabled.

## Cost-conscious deployment

This keeps zero warm instances, one maximum service instance, one task per research shift, no
retries, and no public access. It never upgrades or activates the billing account; it only spends
the already-active free-trial credits attached to the project.

```bash
gcloud run deploy cloud-research \
  --source=. \
  --project=x-cycling-506610-p8 \
  --region=us-central1 \
  --service-account=cloud-research-run@x-cycling-506610-p8.iam.gserviceaccount.com \
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=x-cycling-506610-p8,GOOGLE_CLOUD_LOCATION=global,CLOUD_RESEARCH_MODEL=gemini-3.7-flash,CLOUD_RESEARCH_LIVE_MODEL=gemini-live-2.5-flash-native-audio,CLOUD_RESEARCH_VERTEX_PROJECT=x-cycling-506610-p8,CLOUD_RESEARCH_VERTEX_LOCATION=us-central1,CLOUD_RESEARCH_FIRESTORE_DATABASE='(default)' \
  --min-instances=0 \
  --max-instances=1 \
  --cpu=1 \
  --memory=1Gi \
  --timeout=3600 \
  --no-allow-unauthenticated
```

Reuse the exact built image for the background research job, then tell the service its job name:

```bash
IMAGE="$(gcloud run services describe cloud-research \
  --project=x-cycling-506610-p8 \
  --region=us-central1 \
  --format='value(spec.template.spec.containers[0].image)')"

gcloud run jobs create cloud-research-shift \
  --image="$IMAGE" \
  --project=x-cycling-506610-p8 \
  --region=us-central1 \
  --service-account=cloud-research-run@x-cycling-506610-p8.iam.gserviceaccount.com \
  --command=/workspace/.venv/bin/python \
  --args=-m,app.job \
  --tasks=1 \
  --parallelism=1 \
  --max-retries=0 \
  --task-timeout=3600 \
  --cpu=1 \
  --memory=1Gi \
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=x-cycling-506610-p8,GOOGLE_CLOUD_LOCATION=global,CLOUD_RESEARCH_MODEL=gemini-3.7-flash

gcloud run jobs add-iam-policy-binding cloud-research-shift \
  --project=x-cycling-506610-p8 \
  --region=us-central1 \
  --member="serviceAccount:cloud-research-run@x-cycling-506610-p8.iam.gserviceaccount.com" \
  --role="roles/run.jobsExecutorWithOverrides"

gcloud run services update cloud-research \
  --project=x-cycling-506610-p8 \
  --region=us-central1 \
  --update-env-vars=CLOUD_RESEARCH_JOB=cloud-research-shift,CLOUD_RESEARCH_JOB_LOCATION=us-central1
```

The service calls the Cloud Run Jobs API once and returns Google's operation name plus a UUID. Its
execution override includes the brief, run ID, and selected `LabSpec`. The Job reconstructs that
exact ADK panel and appends structured facts for real ADK authors and agent calls. The private
service reads those facts from Firestore, with Cloud Logging as an operational fallback. The browser
stores only the run ID so it can rejoin after refresh. It does not invent a scientific workflow,
keep a custom queue, or use a research state machine.

Do **not** click **Activate**, **Upgrade**, or convert the free trial to a paid account. Before any
deployment, verify that the Cloud Console billing banner still says **Free trial** and shows the
remaining credit.

## Public event gateway

The model surface remains authenticated. Only a separate two-route ASGI app is public:
`/healthz` and `/api/github/events`. It verifies GitHub's HMAC-SHA256 signature before reading the
payload, deduplicates the delivery in Firestore, and can launch only `cloud-research-shift`.

It runs as `cloud-research-events` with its own identity,
`cloud-research-events@x-cycling-506610-p8.iam.gserviceaccount.com`. That identity has only:

- `roles/run.jobsExecutorWithOverrides` on the one Job;
- `roles/datastore.user` for delivery facts;
- Secret Accessor on `cloud-research-webhook-secret` only.

It has no Vertex role, no Logging Viewer role, and no access to the GitHub publishing token.

```bash
gcloud run deploy cloud-research-events \
  --source=. \
  --command=/workspace/.venv/bin/uvicorn \
  --args=app.webhook_app:app,--host,0.0.0.0,--port,8080 \
  --service-account=cloud-research-events@x-cycling-506610-p8.iam.gserviceaccount.com \
  --region=us-central1 --project=x-cycling-506610-p8 \
  --set-env-vars='GOOGLE_CLOUD_PROJECT=x-cycling-506610-p8,CLOUD_RESEARCH_FIRESTORE_DATABASE=(default),CLOUD_RESEARCH_JOB=cloud-research-shift,CLOUD_RESEARCH_JOB_LOCATION=us-central1' \
  --set-secrets=GITHUB_WEBHOOK_SECRET=cloud-research-webhook-secret:latest \
  --min-instances=0 --max-instances=1 --concurrency=20 --memory=512Mi \
  --allow-unauthenticated
```

An external GitHub ping and a real Issue `labeled` delivery both returned HTTP 200. The latter
launched `cloud-research-shift-6mnfr`, which completed successfully and published a research branch.

## GitHub handoff

When `GITHUB_TOKEN` and `GITHUB_REPOSITORY` are injected as environment variables (preferably from
Secret Manager), Writer creates or updates a `cloud-research/*` branch. Without them, the complete
handoff remains in Cloud Run logs and the local artifact directory. No credential from the
existing research system is ever copied into this project.
