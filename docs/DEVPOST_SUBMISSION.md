# Devpost submission copy

## Project name

Cloud Research

## Elevator pitch

Cloud Research turns every researcher into the PI of a 24/7 panel of Gemini experts—searching,
challenging, experimenting, writing, and explaining until there is an evidence-backed handoff.

## Inspiration

Research rarely stops because the scientist ran out of intelligence. It stops because human
attention is serial. Papers wait to be searched, implementations wait to be checked, cheap
counterexamples wait to be run, failures wait to be understood, and the entire program pauses the
moment the researcher steps away.

We asked a more interesting question: what if a researcher could become the PI of a persistent
expert panel? Not an AI that replaces the scientist, and not another system that summarizes
papers—a research lab that preserves momentum while the human sleeps, studies, teaches, or works
on something else.

## What it does

The researcher gives Cloud Research one brief: the field, current question, known attempts,
compute budget, and what would make the next handoff useful. A Gemini Research Director recruits
the useful specialists in whatever order the evidence demands. The default Lab includes:

- Finder searches for mechanism-level cracks and the nearest prior work.
- Theorist turns the crack into a precise claim, prediction, proof, or counterexample.
- Experimentalist runs the cheapest decisive Python probe in Gemini's isolated code environment.
- Critic attacks novelty, mechanism, and alternative explanations—then proposes the strongest repair.
- Writer preserves evidence, failures, and the next move in a research packet and GitHub branch.
- Explainer reconstructs what happened so the human truly understands and can challenge it.

The background shift runs as a Cloud Run Job, so closing the browser does not stop the research.
The current Lab definition and run ID travel with the Job. A signed GitHub Issue label can start
the same shift without an open browser. Firestore preserves append-only run facts across
scale-to-zero, and Writer publishes the final research packet to a dedicated GitHub branch. When
the human returns, the interface reconstructs the same run and offers a live voice debrief—not a
fabricated progress animation or another chat transcript.

## How we built it

Cloud Research uses Gemini 3.7 Flash through Vertex AI, Google ADK 2.7.1, Cloud Run, and Firestore. One ADK
Director sees every custom specialist as an ADK `AgentTool` and decides dynamically whom to call
and when. Every expert can use Google Search grounding. Roles that describe experiments receive
Gemini built-in code execution; writing roles receive artifact and GitHub publishing tools; theory
roles receive a cheap claim-comparison tool. Explainer is available both inside a research shift
and as a standalone paper, task, research, or result explanation mode.

The private HTTPS service and long-running Job share one container. A separate, public, minimal
event gateway exposes only a health check and HMAC-verified GitHub webhook. The gateway deduplicates
deliveries and launches a Job with the selected Lab specification. The Job owns no scientific state
machine: it gives the brief to the Director, appends real Agent facts to Firestore, publishes the
handoff, and exits. Cloud Run handles lifetime, retry policy, and scale-to-zero.

The research taste came from our existing local research system, but we deliberately did not copy
its process machinery, databases, secrets, queues, watchdogs, or GPU launchers. We ported only the
scientific insight: trust that valuable research fruit exists, remain brutal about whether the
current candidate is it, and treat failures as fuel for a stronger explanation.

## Challenges we ran into

The hardest design problem was not adding more orchestration. It was deleting it. A conventional
agent system wants stages, statuses, gates, and routing rules. Research does not know its next step
in advance. Encoding the expected path would make the system look reliable while quietly making
it less scientific.

We instead put judgment in short prompts and left the runtime thin. That required trusting Gemini
to choose experts dynamically while keeping every expert's role sharp enough to produce useful
work. We also separated cheap cloud probes from expensive local GPU experiments: the cloud shift
can falsify and narrow; the existing local lab can continue a GitHub branch when heavy compute is
actually justified.

The other hard problem was evidence honesty. In a three-case live evaluation, 23 of 24 unique
source URLs resolved; one model-generated GitHub link did not. We preserved that failure and added
a repeatable transport audit instead of editing the score. Reachability still does not prove claim
support—the PI and Critic must inspect that relationship.

## Accomplishments that we're proud of

- A genuine multi-agent panel whose order is model-selected, not a disguised workflow graph.
- A background Cloud Run Job that survives the browser and scales to zero afterward.
- A real GitHub Issue label → signed Cloud Run event → custom Gemini panel → GitHub branch path.
- A resumable interface backed by an append-only Firestore fact ledger.
- An Explainer that makes research legible without turning it into marketing copy.
- Gemini-native grounded search and isolated code probes with no arbitrary local code execution.
- Three completed cross-domain Jobs with reproducible outcome and source-transport audits.
- A second Google model, Gemini Live native audio, proven end-to-end with grounded Handoff context,
  audio frames, transcription, interruption-ready streaming, and a separate Vertex region.
- One private model surface, one tiny public webhook surface, Secret Manager, HMAC verification,
  delivery deduplication, least-privilege IAM, and zero minimum instances.

## What we learned

The most useful autonomy is not the absence of a human. It is continuity around a human. The human
should decide what is worth caring about; the agent team should prevent that decision from
collapsing into hundreds of forgotten intermediate chores.

We also learned that optimism and rigor reinforce each other. “Believe a valuable opening exists”
is what lets the system kill weak candidates aggressively without becoming timid or settling for a
boring report.

## What's next for Cloud Research

Next we will make the human–lab relationship richer without turning it into approval theater: a
living research portfolio across multiple shifts, direct pickup by local GPU experiment agents,
paper-to-experiment lineage, claim-level source-support audits, and Handoffs that teach the
researcher how every important claim changed. The north star remains simple: research should keep
moving, and the human should understand where it moved and why.
