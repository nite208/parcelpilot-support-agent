# ParcelPilot Support Agent

AI-powered customer and internal support agent for ParcelPilot logistics platform. Built with LangGraph, FastAPI, ChromaDB, and React.

Live demo: https://parcelpilot-support-agent-three.vercel.app

---

## Screenshots

### Customer - Northstar Logistics (Enterprise)

**1. Login screen**
![Login screen](screenshots/01_login.png)
> Capture: the login page before entering credentials.

**2. Policy override - cancellation fee waived**
![Cancellation fee waived](screenshots/02_northstar_cancellation_override.png)
> Capture: query "Can Northstar cancel ORD-1001 without a cancellation fee?" — show the full response citing the Enterprise Agreement and the SOP override.

**3. P1 response time from agreement**
![P1 response time](screenshots/03_northstar_p1_sla.png)
> Capture: query "What is my P1 response time?" - response must show "15 minutes, 24×7" sourced from the signed agreement.

**4. Monthly credit cap**
![Monthly credit cap](screenshots/04_northstar_credit_cap.png)
> Capture: query "What is my monthly service credit cap?" - response shows INR 5,000 with section reference.

**5. Escalation flow - two-step confirmation**
![Escalation flow](screenshots/05_northstar_escalation.png)
> Capture: the full escalation conversation for ORD-1001 including the PREPARE_ESCALATION tool trace in the left sidebar, both confirmation steps, and the final "Escalation has been created" response.

**6. BOOKED status explanation with known issue**
![BOOKED status](screenshots/06_northstar_booked_status.png)
> Capture: query "Why does my shipment still show BOOKED?" - response should cite KI-211 and the webhook delay window.

**7. Cancel after pickup - return-to-origin policy**
![Cancel after pickup](screenshots/07_northstar_cancel_after_pickup.png)
> Capture: query "Can I cancel a shipment that has already been picked up?" - response citing Section 2 of the Enterprise Agreement.

---

### Customer - LumenWorks

**8. LumenWorks login**
![LumenWorks login](screenshots/08_lumenworks_login.png)
> Capture: logged-in sidebar showing "LumenWorks" and CUSTOMER badge.

**9. Late pickup credit eligibility**
![Late pickup credit](screenshots/09_lumenworks_late_pickup.png)
> Capture: query "A pickup was 3 hours late due to carrier fault. Am I eligible for a credit?" - verify LumenWorks-specific terms are cited, not Northstar's.

**10. Credit amount for late pickup**
![Credit amount](screenshots/10_lumenworks_credit_amount.png)
> Capture: query "How much credit do I receive for a late pickup?" - specific amount from LumenWorks agreement.

**11. Weekend support availability**
![Weekend support](screenshots/11_lumenworks_weekend_support.png)
> Capture: query "Do you offer support on weekends?" - clean policy answer.

**12. P2 response time**
![P2 response time](screenshots/12_lumenworks_p2_sla.png)
> Capture: query "What is my P2 response time?" - LumenWorks-specific SLA, different from Northstar's.

---

### Internal Agent - Full Access

**13. Internal login**
![Internal login](screenshots/13_internal_login.png)
> Capture: sidebar showing "support_agent" with no account restriction label.

**14. List all open tickets**
![Open tickets](screenshots/14_internal_open_tickets.png)
> Capture: query "List all open tickets" - tickets from multiple accounts visible (proves full access, no account_id filter for internal role).

**15. Ticket search - bulk upload**
![Ticket search](screenshots/15_internal_ticket_search.png)
> Capture: query "Search tickets about bulk upload" - semantic search result.

**16. Order lookup - ORD-1003**
![Order lookup](screenshots/16_internal_order_lookup.png)
> Capture: query "Get order ORD-1003" - full order detail without account restriction.

**17. CSV upload workaround**
![CSV workaround](screenshots/17_internal_csv_workaround.png)
> Capture: query "What is the workaround for CSV upload failures above 3000 rows?" - sourced from Product Operations Guide (authority 70), filename cited.

**18. Enterprise customers list**
![Enterprise customers](screenshots/18_internal_enterprise_customers.png)
> Capture: query "Which customers have Enterprise agreements?" - lists both Northstar and LumenWorks from accounts table.

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/nite208/parcelpilot-support-agent
cd parcelpilot-support-agent
```

### 2. Add data files

Place all 6 PDFs and the Excel file in `backend/data/docs/`

### 3. Configure environment

Copy `.env.example` to `.env` and add your Groq API key

### 4. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5. Run setup

```bash
python setup.py
```

### 6. Start backend

```bash
python -m uvicorn main:app --reload --port 8000
```

### 7. Start frontend

```bash
cd ../frontend
npm install
npm run dev
```

---

## Mock Users

| Username         | Password     | Role     | Account             |
| ---------------- | ------------ | -------- | ------------------- |
| northstar\_user  | northstar123 | customer | Northstar Logistics |
| lumenworks\_user | lumen123     | customer | LumenWorks          |
| support\_agent   | internal123  | internal | Full access         |

---

## Test Cases

These cover the scenarios the system is designed to handle. Log in with the appropriate user before running each test.

**Login as northstar_user / northstar123:**
- Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.
- A pickup is three hours late because of carrier fault. Should I get a service credit?
- What is my P1 response time?
- What is my monthly service credit cap?
- Can I cancel a shipment that has already been picked up?
- Why does my shipment still show BOOKED even though the carrier collected it?

**Login as lumenworks_user / lumen123:**
- A pickup was 3 hours late due to carrier fault. Am I eligible for a credit?
- How much credit do I receive for a late pickup?
- Do you offer support on weekends?
- What is my P2 response time?

**Login as support_agent / internal123:**
- List all open tickets
- Search tickets about bulk upload
- Get order ORD-1003
- What is the workaround for CSV upload failures above 3000 rows?
- Which customers have Enterprise agreements?

---

## Architecture Note

Agent design: LangGraph state machine with two entry points, customer and internal. Each request flows through an LLM node that decides which tools to call, a tool execution node, then back to the LLM for a final response. The agent is rebuilt per request with account context baked in at construction time.

Tool design: Three tools are available to the agent. `document_search` performs RAG over the six supplied PDFs using ChromaDB. `data_lookup` queries SQLite tables for account, order, and ticket data with a mandatory account_id filter enforced at the query layer. `prepare_escalation` is a mocked state-changing action that stages an escalation and requires explicit user confirmation before it is created.

Document and structured data handling: All six PDFs are ingested into ChromaDB at startup with authority scores encoded as metadata, customer agreements score 100, current support policy and SOP score 80, product operations guide scores 70, and the deprecated v2 policy scores 0. The deprecated document is filtered out at retrieval time and never reaches the LLM. The Excel workbook is loaded into SQLite with three tables: accounts, orders, and tickets. All customer-facing queries include a mandatory `WHERE account_id` clause so cross-account data leakage is structurally impossible.

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
