# Google Cloud setup

Project: `Cloud Research`  
Project ID: `x-cycling-506610-p8`  
Model: `gemini-3.7-flash`
Live Audio model: `gemini-live-2.5-flash-native-audio`

Cloud Research uses exactly the three competition layers:

1. **Gemini API through Vertex AI** for reasoning, Google Search grounding, and built-in code execution.
2. **Google ADK** for the Director and six model-selected expert agents.
3. **Cloud Run** for the HTTPS surface plus a durable one-shot Job that survives the browser.

## APIs

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  logging.googleapis.com \
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
```

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
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=x-cycling-506610-p8,GOOGLE_CLOUD_LOCATION=global,CLOUD_RESEARCH_MODEL=gemini-3.7-flash \
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
exact ADK panel and prints structured events for real ADK authors and agent calls. The private
service reads those events from Cloud Logging; the browser stores only the run ID so it can rejoin
after refresh. It does not invent a scientific workflow, keep a custom queue, or use a research
state machine.

Do **not** click **Activate**, **Upgrade**, or convert the free trial to a paid account. Before any
deployment, verify that the Cloud Console billing banner still says **Free trial** and shows the
remaining credit.

## Optional GitHub handoff

When `GITHUB_TOKEN` and `GITHUB_REPOSITORY` are injected as environment variables (preferably from
Secret Manager), Writer creates or updates a `cloud-research/*` branch. Without them, the complete
handoff remains in Cloud Run logs and the local artifact directory. No credential from the
existing research system is ever copied into this project.
