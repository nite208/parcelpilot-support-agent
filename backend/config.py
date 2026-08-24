import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./backend/chroma_store")
DATA_DIR = os.getenv("DATA_DIR", "./backend/data/docs")
DB_PATH = os.getenv("DB_PATH", "./backend/data/parcelpilot.db")

DOCUMENT_AUTHORITY = {
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": 100,
    "06_LumenWorks_Service_Agreement.pdf": 100,
    "01_Support_Policy_v3_CURRENT.pdf": 80,
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": 80,
    "04_Product_Operations_Guide_and_Known_Issues.pdf": 70,
    "02_Support_Policy_v2_DEPRECATED.pdf": 0,
}

DEPRECATED_DOCS = {"02_Support_Policy_v2_DEPRECATED.pdf"}

MOCK_USERS = {
    "northstar_user": {
        "password": "northstar123",
        "role": "customer",
        "account_id": "ACCT-001",
        "account_name": "Northstar Logistics"
    },
    "lumenworks_user": {
        "password": "lumen123",
        "role": "customer",
        "account_id": "ACCT-002",
        "account_name": "LumenWorks"
    },
    "support_agent": {
        "password": "internal123",
        "role": "internal",
        "account_id": None,
        "account_name": None
    },
}