# ParcelPilot Support Agent

AI-powered customer and internal support agent for ParcelPilot logistics platform.

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
uvicorn main:app --reload --port 8000

### 7. Start frontend
cd ../frontend
npm install
npm run dev

## Mock Users

| Username | Password | Role | Account |
|---|---|---|---|
| northstar_user | northstar123 | customer | Northstar Logistics |
| lumenworks_user | lumen123 | customer | LumenWorks |
| support_agent | internal123 | internal | Full access |

## Architecture

- LangGraph multi-agent orchestration
- LlamaIndex + ChromaDB RAG with authority scoring
- SQLite structured data with account-level isolation
- FastAPI backend with JWT auth
- React frontend with tool trace sidebar