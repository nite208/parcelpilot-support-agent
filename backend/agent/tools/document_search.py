import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain.tools import tool
from rag.retriever import retrieve


def build_document_search_tool(account_id=None, role="customer"):
    
    @tool
    def document_search(query: str) -> str:
        """
        Search ParcelPilot policy documents, SOPs, customer agreements, and product guides.
        Use this to answer questions about support SLAs, cancellation rules, service credits,
        product capabilities, and known issues.
        """
        results = retrieve(query, account_id=account_id)
        
        if not results:
            return "No relevant documents found for this query."
        
        output_parts = []
        
        for i, r in enumerate(results):
            source = r["source"]
            page = r["page"]
            authority = r["authority"]
            content = r["content"]
            
            if authority == 100:
                trust_label = "HIGH AUTHORITY - Customer Agreement"
            elif authority >= 70:
                trust_label = "AUTHORITATIVE - Current Policy"
            else:
                trust_label = "REFERENCE"
            
            part = f"[Source {i+1}] {source} (Page {page}) | {trust_label}\n{content}"
            output_parts.append(part)
        
        return "\n\n---\n\n".join(output_parts)
    
    return document_search