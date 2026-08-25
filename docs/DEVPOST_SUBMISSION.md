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
six specialists in whatever order the evidence demands:

- Finder searches for mechanism-level cracks and the nearest prior work.
- Theorist turns the crack into a precise claim, prediction, proof, or counterexample.
- Experimentalist runs the cheapest decisive Python probe in Gemini's isolated code environment.
- Critic attacks novelty, mechanism, and alternative explanations—then proposes the strongest repair.
- Writer preserves evidence, failures, and the next move in a research packet and GitHub branch.
- Explainer reconstructs what happened so the human truly understands and can challenge it.

The background shift runs as a Cloud Run Job, so closing the browser does not stop the research.
The human returns to an evidence-backed handoff, not a chat transcript.

## How we built it

Cloud Research uses Gemini 3.7 Flash through Vertex AI, Google ADK 2.7.1, and Cloud Run. One ADK
Director sees six specialist agents as tools and decides dynamically whom to call and when. Finder
uses Google Search grounding; Experimentalist uses Gemini built-in code execution; Writer can
publish a durable GitHub research packet; Explainer is available both inside a research shift and
as a standalone paper-explanation mode.

The HTTPS service and long-running Job share one container. The service accepts the research
contract and launches one Job execution. The Job owns no scientific state machine: it gives the
brief to the Director, streams evidence to Cloud Logging, publishes the handoff, and exits. Cloud
Run handles lifetime and scale-to-zero.

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

## Accomplishments that we're proud of

- A genuine multi-agent panel whose order is model-selected, not a disguised workflow graph.
- A background Cloud Run Job that survives the browser and scales to zero afterward.
- An Explainer that makes research legible without turning it into marketing copy.
- Gemini-native grounded search and isolated code probes with no arbitrary local code execution.
- One container and a small deterministic core, with no imported runtime or secrets from the
  existing system.
- A complete offline verification suite: agent wiring, prompts, tools, server, UI, and container.

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
paper-to-experiment lineage, and Morning Handoffs that teach the researcher how every important
claim changed. The north star remains simple: research should keep moving, and the human should
understand where it moved and why.

