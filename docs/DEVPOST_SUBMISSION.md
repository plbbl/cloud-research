## Inspiration

The next bottleneck in research may not be a shortage of intelligence. It may be **human
bandwidth**.

AI's potential in research is no longer speculative. Progress in mathematical reasoning,
scientific discovery, coding, and literature analysis suggests that machine researchers will soon
be able to explore more hypotheses, read more papers, and run more intellectual experiments than
any individual human could follow. That creates a new problem: can people still understand,
challenge, and take intellectual ownership of research produced at machine speed?

Most auto-research projects ask: **How much of the scientist can we remove from the loop?** That
frames the human as latency. We reject that premise. Research is not complete when a system emits
an answer or a paper. It becomes useful when a person can understand it, contest it, reproduce it,
and decide what it means. The more consequential question is: **How much more capable can a
scientist become when AI works around them?**

A researcher should not have to personally push every intermediate step forward. Searching the
latest work, checking code, comparing mechanisms, running a cheap counterexample, recording a dead
end, and turning scattered evidence into the next decisive question all consume the same scarce
resource: human attention. When the researcher sleeps, teaches, studies, or focuses on another
problem, those processes usually stop.

Cloud Research began with a different vision: give every researcher a persistent research
institution of their own. The human remains the PI—the source of purpose, taste, judgment, and
responsibility. A panel of AI researchers maintains momentum around that human, and an Explainer
makes every important result re-enterable. The goal is not research without people. The goal is to
let people think at the scale of the research world they now inhabit.

## What it does

The researcher creates a Lab, defines the experts it needs, and gives it one brief: the field, the
current question, prior attempts, constraints, compute budget, and what a useful handoff should
contain. A Gemini Research Director reads that brief and recruits specialists in whatever order the
evidence demands.

A typical Lab contains:

- **Finder**, which searches current papers, code, and nearby ideas for the real opening rather than
  a keyword-level gap.
- **Theorist**, which turns an opening into a precise mechanism, prediction, proof, or
  counterexample.
- **Experimentalist**, which runs the cheapest decisive probe before recommending expensive
  compute.
- **Critic**, which attacks novelty, evidence, assumptions, and alternative explanations, then
  proposes the strongest repair.
- **Writer**, which preserves sources, claims, failed paths, artifacts, and the next executable
  research task.
- **Explainer**, which reconstructs a paper, task, experiment, or full research shift so the human
  understands not only *what* the Lab concluded, but *why* its beliefs changed.

These are defaults, not a fixed organization chart. The human can create multiple Labs; add,
remove, rename, and rewrite roles; address the whole panel; or `@` one expert directly. The
Director can call experts repeatedly and in any order. There is no scripted scientific state
machine pretending to know the shape of a discovery in advance.

When the researcher leaves, the same Lab continues as a Cloud Run Job. It can search with live
Google grounding, compare claims, run isolated Python probes, challenge weak directions, preserve
failures, and produce an evidence-backed Handoff. Firestore records the Lab, run, expert events,
artifacts, and final Handoff across scale-to-zero and browser departure. A signed GitHub Issue label
can launch a shift without an open tab, and Writer can prepare the research packet on a dedicated
GitHub branch.

When the human returns, Cloud Research does not present a magical final answer. It presents a
research inheritance:

- what the Lab investigated;
- which candidates survived and which were killed;
- what evidence changed the argument;
- what remains unknown;
- which cheap experiments were run;
- what deserves the researcher's attention next; and
- how to continue the work locally or in the cloud.

The researcher can then question the Explainer in text or speak with the animated Lab Bot through
Gemini Live. Human participation happens where it matters—setting direction, interrogating
evidence, changing the team, and making scientific judgments—not through an endless sequence of
approval buttons.

## How we built it

Cloud Research uses **Gemini 3.7 Flash through Vertex AI**, **Google ADK 2.7.1**, **Cloud Run**, and
**Cloud Firestore**. Gemini Live provides the native-audio debrief with the central Lab Bot.

At the center is one ADK Director. Every custom specialist is exposed to it as an ADK `AgentTool`.
The Director sees the brief, the current evidence, and the available experts, then decides whom to
call next. Google Search grounding is available to research roles. Experimental roles receive
Gemini's isolated code execution. Writing roles receive artifact and GitHub tools. Explainer can be
called inside a research shift or used independently for a paper, task, result, or previous Handoff.

The cloud architecture separates interaction from durable execution:

1. A private Cloud Run service hosts the Lab interface and accepts authenticated briefs.
2. A Cloud Run Job owns the long research shift, so closing the browser does not terminate it.
3. Firestore acts as an append-only fact ledger for Labs, expert events, delivery records,
   artifacts, and Handoffs.
4. A minimal public Cloud Run gateway verifies HMAC-signed GitHub webhooks, rejects duplicate
   deliveries, selects the requested Lab, and launches the Job.
5. Secret Manager and separate service identities keep the public event surface isolated from the
   private research surface.

We deliberately kept the scientific runtime thin. Cloud Run manages lifetime, retries, and
scale-to-zero; Firestore remembers facts; ADK exposes specialists; Gemini decides the scientific
move. Our prompts carry three pieces of research taste:

- **Concise:** give the expert a sharp responsibility, not a policy manual.
- **Excited:** pursue the crack that could change understanding; research should remain deeply
  interesting.
- **Certain:** trust that valuable research fruit exists, even when the current candidate is wrong.

The shared operating belief is: **Trust the opportunity. Doubt the candidate. Keep going.**

Cloud Research was built from scratch during the hackathon submission period. The application,
research architecture, prompts, custom roles, interface, Cloud Run surfaces, Firestore ledger,
GitHub gateway, Live experience, and deployment were created specifically for this project.

## Challenges we ran into

The first challenge was resisting the temptation to encode research as a workflow diagram. A
conventional multi-agent system wants stages, gates, statuses, and deterministic routing. Real
research is not known in advance. A source can invalidate the premise; a critic can expose a
missing variable; a four-line probe can make an entire direction irrelevant. Hard-coding the path
would make the demo look orderly while making the Lab less intelligent.

We solved this by putting scientific judgment in short expert prompts and letting the ADK Director
choose the path. The code manages capabilities and persistence, not scientific taste.

The second challenge was making autonomy legible. A system that performs many actions while the
human is away can easily become alienating: the user returns to conclusions they did not witness
and cannot reconstruct. We therefore treated explanation as a first-class research capability,
not a summary generated at the end. Expert messages, failed hypotheses, sources, experiments, and
belief changes remain available to the Explainer and to the human PI.

The third challenge was continuity. A browser request is short-lived; a serious research shift is
not. We had to carry a custom Lab definition and run identity into a background Job, stream real
expert events back into the interface, survive refreshes and cold starts, and reconstruct the same
Handoff from Firestore when the researcher returned.

The fourth challenge was evidence honesty. Grounded models can still produce weak associations or
bad links. In our source-transport audit, 23 of 24 unique URLs resolved and one generated GitHub URL
returned 404. We preserved that failure instead of editing it away. Reachability is not scientific
support; it is only one auditable layer in the evidence chain. The Critic and human PI still need
to judge whether a source actually supports a claim.

Finally, we had to make a sophisticated system feel calm. Multiple Labs, custom experts, live
events, voice, background execution, and durable artifacts could easily become a dashboard full of
status machinery. We designed the interface as a research room: one conversation, a visible team,
a fluid Lab Bot, and a Handoff that teaches rather than overwhelms.

## Accomplishments that we're proud of

- We built a genuine model-directed expert panel whose order is selected by evidence, not by a
  disguised workflow graph.
- A research shift survives the browser as a Cloud Run Job and scales back to zero when finished.
- Researchers can create multiple Labs and completely rewrite the number, identity, and role of
  their experts.
- A real signed GitHub event can launch the selected Gemini Lab, preserve its events in Firestore,
  and create a research branch without an open browser.
- Explainer supports papers, tasks, results, and the Lab's own work, making comprehension part of
  the product rather than an afterthought.
- Gemini Live provides an interruption-ready voice debrief grounded in the current Handoff, with
  the Lab Bot visibly listening, thinking, and speaking.
- Three cross-domain research Jobs completed with seven to eight real expert events each, including
  killed paths, unknowns, source lists, artifacts, and next actions.
- A separate bounded Cloud Run proof path completed five consecutive executions with one succeeded
  task and exit code `0` in every run.
- The public surface is reduced to a health endpoint and a verified GitHub gateway; the research
  service, Lab data, model calls, and Live sessions remain private.

What we are proudest of is not that the system can produce more research text. It is that the Lab
can work independently without pushing the human out of the intellectual process.

## What we learned

We learned that the real unit of research is not a task. It is a continuing argument between ideas,
evidence, experiments, critics, and people. A useful research agent therefore needs continuity and
memory more than a longer answer box.

We learned that autonomy without legibility is a weak form of augmentation. If the human cannot
inherit the reasoning, uncertainty, and next question, the system has accelerated output while
slowing understanding. Explanation is not presentation polish; it is the interface through which
agency returns to the researcher.

We learned that multi-agent value does not come from showing many avatars. It comes from productive
differences: one expert searches, another commits to a mechanism, another tries to destroy it, and
another preserves what changed. The disagreement is the feature.

We also learned that optimism and rigor are allies. Believing that an important opening exists
gives the Lab permission to reject weak candidates without becoming timid. A failed hypothesis is
useful when it is preserved as information and converted into a sharper next move.

Most importantly, we learned that the best role for AI in research is not simply replacing human
labor. It is expanding human scientific agency: giving one person more eyes, more critics, more
working memory, and more uninterrupted time—while keeping meaning and responsibility with the
person.

## What's next for Cloud Research

The next step is to turn one research shift into a living research program.

We want persistent claim lineage across weeks: which source introduced a belief, which experiment
changed it, which critic challenged it, and which later result repaired or rejected it. We want
every Handoff to connect to the next Lab shift instead of becoming another forgotten report.

We will add secure compute bridges that let a researcher attach their own CPU or GPU server. Cloud
agents will be able to prepare a bounded experiment, hand it to authorized compute, observe the
result, and bring the evidence back into the same research conversation. Heavy compute remains a
resource owned by the human; the Lab makes it easier to use deliberately.

We also want teams of humans to participate in the same research institution: multiple PIs,
student–advisor handoffs, domain-specific Labs, replication panels, and an Explainer that adapts to
what each collaborator already understands. Claim-level source audits and reproducible experiment
lineage will make the system increasingly suitable for serious scientific work.

The long-term vision is not a machine that publishes while people watch. It is a new interface
between human curiosity and machine-scale exploration—a place where AI keeps research moving and
humans can keep understanding, questioning, and deciding what the research means.
