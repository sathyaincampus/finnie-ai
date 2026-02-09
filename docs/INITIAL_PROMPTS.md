# Finnie AI — Initial Prompts

> These are the two prompts that kicked off the entire Finnie AI project.  
> Prompt 1 generated the full technical specification (SPEC_DEV.md).  
> Prompt 2 refined the architecture, reprioritized the roadmap, and shaped the final design.  
> Everything else after this was just "build it", "fix this", and "add that."

---

## Prompt 1 — The Big Spec Prompt

```
ACT AS: Principal AI Architect & Engineering Lead.
PROJECT: "Finnie AI" (Evolution: Autonomous Financial Intelligence System).
GOAL: Create the source-of-truth documentation (SPEC_DEV.md and ROADMAP.md) for an
Interview Kickstart Capstone project that achieves a perfect 100/100 score while
demonstrating mastery of the full GenAI stack (from scratch-transformers to agentic
orchestration).

CONTEXT: I must build "Finnie AI," a multi-agent financial assistant. However, I want
to over-engineer this intentionally to use it as a learning vehicle for advanced
concepts. We will not just build a chatbot; we will build a "Hedge Fund in a Box"
architecture.

CONSTRAINTS & RUBRIC (Must Achieve "Excellent" in all categories):
1. Technical (40%): Must use 6+ specialized agents, LangGraph state machines (not
   just chains), GraphRAG (Neo4j + Vectors), and robust error handling.
2. UX (25%): Multi-tab interface (Streamlit/React), natural flow, professional
   financial visualizations.
3. Domain (20%): 100+ article Knowledge Base, real-time market data (yFinance),
   portfolio analysis.
4. Quality (15%): Modular code, 90%+ test coverage, comprehensive docs.
5. Innovation (Bonus): We will secure these points by implementing Voice Mode and
   On-Device Local LLM routing.

MANDATORY TECHNICAL CONCEPTS TO INTEGRATE:
You must find a logical place in the architecture for ALL of the following:
1. BPE & Transformers (Build a small "Router" model from scratch to classify query
   complexity).
2. RAG + Knowledge Graph (GraphRAG for connecting entities like "Tesla" -> "EV Sector"
   -> "Regulatory Risk").
3. Fine-Tuning (PEFT/LoRA) & Quantization (Train a local Llama-3 model on financial
   definitions for cost-savings).
4. Distillation (Use GPT-4 to teach the smaller local model).
5. Agentic AI (MCP, A2A communication, LangGraph cycles).

DELIVERABLE 1: SPEC_DEV.md
Create a comprehensive technical specification file. It must include:
- System Architecture Diagram (Mermaid): Showing the flow between User -> Custom
  Router (Transformer) -> LangGraph Orchestrator -> 6 Agents -> Tools.
- Agent Roster: Define 6 agents (e.g., "The Quant" for data, "The Guardian" for
  compliance, "The Professor" for education).
- Data Layer: Schema for the Vector DB + Knowledge Graph (Neo4j).
- Tech Stack: Explicitly list libraries for every concept (PyTorch for BPE, LangGraph
  for orchestration, Unsloth for Fine-tuning).

DELIVERABLE 2: ROADMAP.md
Create a phased execution strategy to build this without getting overwhelmed.
- Phase 1: The Engine (Foundations): Building the BPE Tokenizer and Custom Router
  from scratch.
- Phase 2: The Brain (Knowledge): Setting up GraphRAG and ingestion pipelines.
- Phase 3: The Body (Agents): Implementing the LangGraph state machine.
- Phase 4: Optimization (The "Synapse" Layer): Fine-tuning, Quantization, and
  Distillation steps.
- Phase 5: The Face (UX): Streamlit UI and Voice integration.

For each phase, list the "Pros/Cons" of the architectural choices.

Please pause after generating these two files so we can review the architecture
before writing a single line of code. Start by generating the SPEC_DEV.md.
Here are the files for you to refer for project requirements, given as images
and also excel.
```

*I also attached images of the capstone requirements and scoring rubric here.*

---

## Prompt 2 — Refining the Spec (The Big Follow-Up)

> After getting the first version of the spec, I had a bunch of questions and changes. I typed this all out in one go.

```
Couple of questions or pointers

1. The underlying layers seems to take more time, first lets plan and have the spec
and roadmap in a way that we can build the important parts needed for the capstone
project like the LangGraph agents, memory, UI, etc. as mentioned in the requirement
images I gave and later we can dig deeper into the underpinnings of LLM like BPE,
Transformer, LoRA, Fine tuning, Quantization, local training, distillation, etc.
We can go with cloud based LLM and then have option to switch to these local LLMs
which we would implement later. I believe based on the roadmap you have given these
could be added later if time permits and without these also everything should work
end to end, because I have a presentation this weekend which is this Sunday, 3 days
from now to get a presentation ready to show architecture, flow, UI/UX mocks, etc.
which we need to get ready and the submission is expected on next Sunday, which is
roughly 10 days from now. (Note you are the one I mean Claude is the one gonna
implement everything via Antigravity Studio on my MacBook Air M2. So you can do it
faster I believe.) Also we need to see how to add responsive UI and cross platform
like Android, iOS, web, Mac, Windows, Linux to get ahead of other people (we can
add/extend for cross platform at the end though, but at least it needs to be
responsive when viewed on a mobile) and make it usable and also plan to deploy to
Google Cloud, publishing to cloud is also one of the key criteria.

These are the topics I believe could be plugged in later from your roadmap:
- BPE Tokenizer (Scratch)
- Custom Router Transformer
- Router Training & Validation
- Llama-3 LoRA Fine-tuning
- 4-bit Quantization
- Distillation from GPT-4
- Local/Cloud Routing (Probably we can keep routing layer but we can say local won't
  work initially until we implement rest of the layers which we can keep adding one
  by one so everything works as well by having config flags)

Correct me if I'm wrong too.

2. Also I love the idea of your GraphRAG and VectorDB in combination. Just curious
how much data will we ingest and how much time it will take. We can use AuraDB to
ingest instead of local knowledge graph I believe to host easily, I will go by your
suggestion though, as we want to make it run faster too. And regarding the how much
data part, what will happen to the questions that the user asks for which we don't
have knowledge in the GraphRAG. How can we ingest whole market data, how much space
will it occupy? How many years worth of history of data can we ingest? How can we
ingest the live news data that keeps coming in? If we route to LLM, will we still
have same kind of linkage and details like we get from GraphRAG, if we are unable
to find in our GraphRAG. What will be the rough latencies? May be we can phase this
too? Not sure if its key, we can keep it to provide our niche but implement agents
first and then come to this, so at least it works with LLM, then extends to
GraphRAG / vectors for local knowledge, etc. to make it faster and deeper analysis.

3. Also for Postgres we can use like NeonDB so it's easier to host later as well?

3a. Not sure for ChromaDB we can do it locally or if there will be cloud hosting as
well. Not sure what we keep storing here. Any reason why we can't use Redis instead
and use the new embedding feature from Redis as well? Is there a free cloud hosting
for Redis / ChromaDB too like Neon and AuraDB? My instructor said he liked Redis a
lot. Maybe I can get more points ;) But I would leave it to you based on complexity.

4. And we need to add in such a way we should have some settings in our UI / app where
we accept user's key and ask them to select the provider and probably the model like
Claude Opus 4.5, Gemini 2.5 Pro, OpenAI GPT 4o, etc. Ensure to have the appropriate
exact model names. Ensure based on what model they select, the prompts are
understandable for those models, because I believe the prompts differ based on each
model too.

5. Can you please help update specs to have UI/UX mocks as well so I can visualize.

6. And what is our Finnie AI doing, is it just suggesting us about the stocks as an
assistant? What else does it do? Can you compare it to an existing product today like
Robinhood, Etrade, etc. Can you please explain or list the functionalities as well
in the spec and roadmap accordingly.

7. Are 6 agents enough or do you think we can add more to provide a niche?

8. How do we make sure our results are faster and user doesn't feel he is having a
problem by just waiting while asking a question. We might have to have very good TTFT,
also we have to have superior UI which doesn't let the user feel bad by showing
"Thinking... preparing... fetching data..." etc.

9. Where are the MCP and A2A parts which are important, I don't see any note of that
in the spec which is very critical. At least MCP is must, A2A we can add at the end
so we can share it with others too as we are anyways planning to deploy to Google Cloud.

10. Observability is a key thing, we need to embed something like LangFuse or so to
see everything end to end.

11. Also important thing when you answer questions, have a running Implementation
Q&A doc, where you answer my questions rephrased and written neatly in a Q&A format
neatly formatted and understandable later if someone views also my thinking of how I
interacted with you to add more features. Also it has to be a single document instead
of you creating multiple documents in the future by creating a documentation mess.

Also we should have a Code walkthrough guide updated finally and also a UI walkthrough
and how to run guides.

Please update spec and roadmap and also have the single Q&A doc ready.

Also update timeline graphs, sequence diagrams and other diagrams accordingly based
on what we spoke above in a phased out manner as well?

Can we also add some projection kind of stuff like if user invest this much and they
would get this much over time, like some prediction, over 3 months, 6 months, 1 year,
2 year, 3 year, 5 year, 10 year with some stock prediction and performance variables,
so user can get an idea. Those predictions should be meaningful and based on market
trend too.

We could also suggest to invest in such a way that their portfolio is balanced based
on risk etc. like local, foreign investments, index funds, bonds, age, etc.

May be we can get real time stock data bank integrations later as a future roadmap,
want to think in an extendable manner.

Also like a projection chart animated, based on what options user selects.

Always please keep updating spec and roadmap meaningfully.

Note the voice chat should be very hi-fi like the one we have in ChatGPT.

And right now don't start coding — lets just update the spec, roadmap, probably the
Q&A document accordingly.
```
