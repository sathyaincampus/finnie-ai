# Finnie AI — Prompt Journal

> **How I built a multi-agent financial AI by prompting an AI coding assistant**  
> These are my actual prompts — copied from chat history — in the order I gave them.  
> I'm sharing this because my peers at Interview Kickstart asked how I prompted to build this.  
> *This is a living document — new prompts get appended as the project evolves.*

---

## Table of Contents

1. [My Prompting Style](#my-prompting-style)
2. [Phase 1: Spec & Architecture (Day 1)](#phase-1-spec--architecture-day-1)
3. [Phase 2: Start Coding (Day 1–2)](#phase-2-start-coding-day-12)
4. [Phase 3: Testing & Bug Fixes (Day 2–3)](#phase-3-testing--bug-fixes-day-23)
5. [Phase 4: Continue Implementation (Day 3)](#phase-4-continue-implementation-day-3)
6. [Phase 5: Voice Interface (Day 3)](#phase-5-voice-interface-day-3)
7. [Phase 6: LLM & GraphRAG (Day 3–4)](#phase-6-llm--graphrag-day-34)
8. [Phase 7: Documentation & Polish (Day 4)](#phase-7-documentation--polish-day-4)
9. [Phase 8: Presentation & Prompt Journal (Day 4)](#phase-8-presentation--prompt-journal-day-4)
10. [What I Learned](#what-i-learned)

---

## My Prompting Style

I don't use prompt templates or fancy formatting. I just talk to it like a developer colleague. Sometimes I paste error messages, sometimes I attach screenshots. The only prompt I put real thought into was the first one (the spec) — after that it was mostly "fix this", "add that", "why is this not working."

---

## Phase 1: Spec & Architecture (Day 1)

> This was where I spent the most time on a single prompt. I wanted the full architecture locked down before writing any code.

### Prompt 1 — The Big Spec Prompt

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

### Prompt 2 — Refining the Spec (The Big Follow-Up)

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

---

## Phase 2: Start Coding (Day 1–2)

### Prompt 3 — Start building

```
Okay go ahead and start implementing, also update in the Q&A is Redis cloud hosting
free anywhere so I can get an account there meanwhile. I have accounts in AuraDB and
NeonDB already. Also please add UX mocks. Also please generate backend frontend
architecture diagrams like this which you helped generate for previous project before
you implement. Maybe add to spec.
```

### Prompt 4 — How to run?

```
Shall we test the current implementation, can you please tell me how to run?
Instructions documented somewhere?
```

### Prompt 5 — First error

```
While running streamlit and opening on browser got this error:
ModuleNotFoundError: No module named 'src'
File "/Users/sathya/web/python/finnie-ai/src/ui/app.py", line 18, in <module>
    from src.config import get_settings, get_available_providers, get_models_for_provider
```

### Prompt 6 — UI looks bad

```
See the color coding, it's very ugly.
```

*Attached a screenshot of the UI.*

---

## Phase 3: Testing & Bug Fixes (Day 2–3)

### Prompt 7 — Need a test guide

```
Okay it works, can you please provide me a test guide and keep updating it as well
as you increase the features by coding, so I know about all the features and how to
test it and create a demo.
```

### Prompt 8 — Education routing broken

```
Okay this is what I got when I asked "What is P/E ratio?"
"I couldn't find data for the ticker(s): WHAT, RATIO. Please verify the symbol(s)."

Looks like the financial education part didn't work. Same for "Hello". "Help" worked
though, gave something back.
```

### Prompt 9 — Ticker format issues

```
BRK-B — Berkshire Hathaway (tests hyphen in ticker) — when I tried brk.b, brk-b,
brkb nothing worked.

But the other educational stuff works though. Also in portfolio I said AAPL 100
shares $140 but it doesn't ask on which date I invested or at least year. For example
I bought around 2017 or so, later AAPL did a 1:5 stock split and I got 500 shares,
it doesn't calculate that value. Or should I look at my Fidelity or something and
enter current number of shares and cost basis here to save the data to my portfolio
and it would show how much I have based on today's rate? But how would it show how
much I have grown in the past. But I would let you decide and tell me.
```

### Prompt 10 — Delete portfolio position

```
How do I delete a particular position if I add it wrongly instead of clearing all?
```

### Prompt 11 — Chat ordering + ticker format issues *(multiple rounds)*

> Took a few back-and-forth attempts to fix BRK.A / BRK-B ticker formats.
> Attached screenshots showing the broken state.

```
Also 2 more things. The new message is coming after the text box when we ask
something in chat. Also both BRK.A and BRK-A and with $ prefix also doesn't work
for anything.
```
```
Still BRK.A or whatever format is not working. Please check the image.
```

### Prompt 12 — Market tab issues

```
Okay that worked, but in the market tab there is no button. Also stock like Apple
doesn't work in market tab. Tried AAPL. Also says "No data found." Whereas same
AAPL in chat tab shows AAPL details.
```

### Prompt 13 — Chart time range + DeepEval *(multiple rounds)*

> The graph zoom/time range took 3–4 rounds of back and forth with screenshots
> before it was fixed. Also asked about LangGraph and DeepEval here.

```
Can we give option to view last 5Y graph? Also are we using LangGraph for our
different agents? And can we use DeepEval for evaluation framework and update
these in our SPEC_DEV and ROADMAP accordingly if it's not there.
```
```
If I select 5 yr nothing is happening, also if I select - also in graph nothing
else is showing up.
```
```
No it doesn't work. When I click the 5Y or 1Y the screen comes back here.
```
```
All good but when I click zoom out it's not doing it properly as you can see, it's
just showing empty around. Is the zoom vertical instead of horizontal / time based?
```

*Attached screenshots for each round showing the broken chart behavior.*

### Prompt 14 — Education fallback not using LLM

```
All good, I just asked this question. Wouldn't that work?
"What are the best investments to do right now with this current market trend?"
Got back: "I'd be happy to explain that concept! However, I need to connect to my
knowledge base for a detailed explanation..."
```

### Prompt 15 — Query parsing issues *(multiple rounds)*

> The agent was misinterpreting natural language queries — treating words like
> "MOVE" and "WEEK" as ticker symbols, or routing to the wrong agent.

```
"How did the market move in the last 1 week?"
Got: Metric MOVE WEEK Price $13.96 (+2.9%) $100.05 (+0.0%)...
```
```
Why is it talking about today? Got: "🌍 Market Movers Today" with just
top gainers and losers...
```
```
"What do you think will move on Monday?"
Got: Clear Secure, Inc. (YOU) Current Price: 33.76...
```

---

## Phase 4: Continue Implementation (Day 3)

### Prompt 16 — Keep going

```
Okay please continue implementation of rest of the phases as per our SPEC_DEV.md.
```

### Prompt 17 — Auto reload?

```
Doesn't Streamlit have an auto reload feature?
```

### Prompt 18 — Monte Carlo error

```
TypeError: OracleAgent._monte_carlo_simulation() got an unexpected keyword argument
'annual_return'
Traceback:
File "/Users/sathya/web/python/finnie-ai/src/ui/app.py", line 722, in
  render_projections_tab
    simulation = agent._monte_carlo_simulation(
        initial, monthly, years,
        annual_return=params["return"],
        annual_std=params["volatility"],
    )
```

### Prompt 19 — Memory + Auth

```
Is there a memory layer to remember across chat conversation and is there a unique
way to implement login or something like passport authentication like Google, GitHub
etc. with minimal details as well so it's always bringing only logged in data of the
customers which they have already chatted with and summarize and use it for further
questions. Make sure to bring a nice UI.
```

### Prompt 20 — Keep going + test guide

```
Okay please continue implementation of rest of the phases as per our SPEC_DEV.md.
```
```
Have you updated the testing guide with new features and how to access them?
```

---

## Phase 5: Voice Interface (Day 3)

### Prompt 21 — Voice debugging *(multiple rounds)*

> Voice was the most iterative feature — took about 5 rounds of back and forth.
> Started with "where is it?", then mic wasn't showing, then audio wasn't playing,
> then needed playback controls.

```
Where is the voice feature and all?
```
```
I don't see any response back.
```
```
Not sure why audio is not working, last time at least the mic icon was showing up
with the text I said but, now even that's not showing up.
```
```
I think you stopped while testing via browser half way. I saw now it's showing mic
icon displaying the text I spoke, responding back the response in UI, but no talking
back. Is it because my server is running somewhere and I didn't restart?
```
```
That's good it spoke back, but unable to stop audio in between — there is no control
for it. And what does it mean by "knowledge tool" here, what should I do to get the
right answers?
```

---

## Phase 6: LLM & GraphRAG (Day 3–4)

### Prompt 22 — API key + LLM not working *(multiple rounds)*

> Discovered that the API key from .env wasn't being loaded into the UI, and the
> Scout agent wasn't using the LLM for analysis.

```
I wanted to change to Gemini 2.5 Flash Lite. Also I have already given my API key
in my .env file before right? Wouldn't that suffice? Why it says GraphRAG is not
connected? Also I don't think it's answering via LLM still even though I gave
the keys.
```
```
"Can you predict how the market is going to move on Monday?"
Got: "🌍 Market Movers — Recent Momentum (past 5 days)..." with just data.
Why is LLM not coming in here and predicting?
```

*Attached a screenshot of the Settings tab.*

### Prompt 23 — Code walkthrough

```
Okay do we already have a code walkthrough document, if not can you please generate
one and keep it up to date going forward whenever we implement anything?
```

### Prompt 24 — DeepEval + Quant vs Scout

```
Okay why are we not talking about DeepEval. Also why do we need:
- Quant (quant.py) — Ticker symbols, "price of" — yFinance real-time
- Scout (scout.py) — "Trending", "Market today" — yFinance + LLM

Isn't this a repeat? Or does it save time by returning faster without accessing LLMs
if user just asks price?
```

### Prompt 25 — Build GraphRAG

```
Ok if I connect GraphRAG what do I feed in that? Where is the script for ingesting
the graph nodes and edges? Can you please explain the concept of what data will be
pushed in and how it will be saved and can you also generate the script for the same
and how and where will it be used when user is asking questions. Also generate code
and code walkthrough update for the same.
```

---

## Phase 7: Documentation & Polish (Day 4)

### Prompt 26 — Data extraction + spec update + presentation

```
Why are you having all of the data inside code like in ingest.py? Being a good
architect / software engineer shouldn't you split that out to separate data source
files like CSV or JSON or whatever so just data can be added later? Also can you
update spec and roadmap for features that we added in ad hoc manner? Also can you
prepare me a PPT for demo of what all we have done, how we have done, etc. for my
capstone project.
```

---

## Phase 8: Presentation & Prompt Journal (Day 4)

### Prompt 27 — Create this document

```
Okay thanks can you add prompt.md file and from the beginning of this project
finnie-ai how I prompted and prepared spec md roadmap etc. and how I kept prompting
further to fix, can you enhance my prompts properly and document it in the prompt
document and keep appending it further as well in future whatever I ask by enhancing
the prompt and saving it so I can share it with others, as my peer students at
Interview Kickstart was asking for how I prompted and got this.
```

---

## What I Learned

1. **The spec prompt is the most important one.** I spent real time on Prompt 1 –
   included the rubric scoring, all the tech requirements, and explicitly said "don't
   code yet." That single prompt defined the whole project. After that, I could just say
   "continue implementing as per SPEC_DEV.md."

2. **Most of my prompts are just bug reports.** Look at Phase 3 — it's mostly "this
   doesn't work" with a screenshot. That's normal. You don't need to write essays.

3. **Screenshots are your best friend.** When something breaks, just paste a screenshot.
   Way more effective than trying to describe what's wrong.

4. **Error messages work as prompts.** Half my prompts are just pasting a Python traceback
   and saying nothing else. The AI figures out the fix.

5. **"Continue as per spec" is a valid prompt.** Once you have a good spec document, you
   can literally just say "continue implementation of rest of the phases as per our
   SPEC_DEV.md" and it knows what to do.

6. **Ask questions inline.** In Prompt 2, I asked 11 questions in one go — about Redis vs
   ChromaDB, NeonDB for Postgres, how much data to ingest, etc. Batching questions is
   more efficient than separate conversations.

7. **Challenge the AI's decisions.** I asked "Why are you having all the data inside
   code?" and "Isn't Quant vs Scout a repeat?" Don't just accept everything — push back
   when something seems wrong.

8. **Keep a single Q&A document.** I explicitly asked for "a single document instead of
   creating multiple documents in the future by creating a documentation mess." This
   saved me from scattered docs.

9. **You don't need fancy prompts after the first one.** Compare Prompt 1 (detailed spec
   with rubric) to Prompt 28 ("Where is the voice feature and all?"). Both got results.
   The spec needed detail; the feature request didn't.

10. **Let the AI own the architecture, but you own the priorities.** I told it what to
    defer (BPE, LoRA, local LLM) and what to prioritize (agents, UI, deployment). The
    AI designed it, I directed it.

---

*Last Updated: February 8, 2026*  
*27 prompts over 4 days across ~8 conversation sessions*

---

## Prompt Append Log

> *New prompts will be added below as the project evolves.*
