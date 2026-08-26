# ParcelPilot Support Agent

AI-powered customer and internal support agent for ParcelPilot logistics platform. Built with LangGraph, FastAPI, ChromaDB, and React.

Live demo: https://parcelpilot-support-agent-three.vercel.app

---

## Setup

### 1. Clone the repo

git clone https://github.com/nite208/parcelpilot-support-agent
cd parcelpilot-support-agent

### 2. Add data files

Place all 6 PDFs and the Excel file in backend/data/docs/

### 3. Configure environment

Copy .env.example to .env and add your Groq API key

### 4. Install dependencies

cd backend
pip install -r requirements.txt

### 5. Run setup

python setup.py

### 6. Start backend

python -m uvicorn main:app --reload --port 8000

### 7. Start frontend

cd ../frontend
npm install
npm run dev

---

## Mock Users

| Username | Password | Role | Account |
|---|---|---|---|
| northstar_user | northstar123 | customer | Northstar Logistics |
| lumenworks_user | lumen123 | customer | LumenWorks |
| support_agent | internal123 | internal | Full access |

---

## Test Cases

These cover the scenarios the system is designed to handle. Log in with the appropriate user before running each test.

Login as northstar_user / northstar123:
- Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.
- A pickup is three hours late because of carrier fault. Should I get a service credit?
- What is my P1 response time?
- What is my monthly service credit cap?
- Can I cancel a shipment that has already been picked up?
- Why does my shipment still show BOOKED even though the carrier collected it?

Login as lumenworks_user / lumen123:
- A pickup was 3 hours late due to carrier fault. Am I eligible for a credit?
- How much credit do I receive for a late pickup?
- Do you offer support on weekends?
- What is my P2 response time?

Login as support_agent / internal123:
- List all open tickets
- Search tickets about bulk upload
- Get order ORD-1003
- What is the workaround for CSV upload failures above 3000 rows?
- Which customers have Enterprise agreements?

---

## Architecture Note

Agent design: LangGraph state machine with two entry points, customer and internal. Each request flows through an LLM node that decides which tools to call, a tool execution node, then back to the LLM for a final response. The agent is rebuilt per request with account context baked in at construction time.

Tool design: Three tools are available to the agent. document_search performs RAG over the six supplied PDFs using ChromaDB. data_lookup queries SQLite tables for account, order, and ticket data with a mandatory account_id filter enforced at the query layer. prepare_escalation is a mocked state-changing action that stages an escalation and requires explicit user confirmation before it is created.

Document and structured data handling: All six PDFs are ingested into ChromaDB at startup with authority scores encoded as metadata, customer agreements score 100, current support policy and SOP score 80, product operations guide scores 70, and the deprecated v2 policy scores 0. The deprecated document is filtered out at retrieval time and never reaches the LLM. The Excel workbook is loaded into SQLite with three tables: accounts, orders, and tickets. All customer-facing queries include a mandatory WHERE account_id clause so cross-account data leakage is structurally impossible.

Source reliability and conflict handling: Customer agreements are tagged as highest priority and surface first in retrieval results. When a customer agreement overrides a default policy rule, the agent is instructed to cite the agreement explicitly and state the override. Historical ticket resolutions are excluded from the retrieval index entirely and treated as context only, consistent with the assessment brief. When sources conflict, the agent surfaces the conflict rather than resolving it silently.

Major trade-offs: ChromaDB default embeddings were used instead of sentence-transformers to stay within an 8GB RAM constraint on the development machine. The Groq free tier was used for LLM inference with the gpt-oss-20b model. The escalation store is in-memory and resets on server restart, which is acceptable for assessment scope but would need a database-backed implementation in production.

---

## Product Note

Additional problem chosen: Problem 2, Trust and Reliability. This was addressed architecturally rather than as a separate surface. Every retrieval response includes the source filename and authority score. Deprecated documents are filtered before the LLM sees them. Customer agreements are explicitly surfaced as overrides of default policy. The system prompts instruct the agent to state conflicts clearly and to escalate rather than guess when carrier fault, pickup timing, or customer fault is unknown, directly reflecting the language in the SOP.

What I would build next: A proactive issue radar for internal users. This would be a background job that clusters open tickets by semantic similarity, flags tickets approaching or breaching SLA, and surfaces multi-customer incidents on an internal dashboard. This directly addresses Problem 1 and would be the highest-value next feature because a reactive chatbot only helps once someone asks, the radar helps before anyone has to ask.

What I left out: Persistent escalation storage, email and Slack notifications on escalation creation, full audit logging of agent decisions, rate limiting per account, and streaming responses in the chat interface.

One metric: Resolution rate without escalation, the percentage of customer queries answered confidently from available sources without requiring human handoff. A rising rate means the knowledge base and agent reasoning are working. A falling rate flags gaps in documentation coverage or retrieval quality and tells the team where to invest next.

---

## AI Tool Usage

Used Claude for architecture planning, system design decisions, and debugging. Used Cursor for code editing and implementation. All code was reviewed, tested, and understood before committing.
