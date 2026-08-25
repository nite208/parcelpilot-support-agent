import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain.tools import tool
from datetime import datetime


ESCALATION_STORE = []


def build_escalation_tool(account_id=None, role="customer"):

    @tool
    def prepare_escalation(query: str) -> str:
        """
        Prepare an escalation for a support ticket or order issue.
        Use this when the user wants to escalate an issue, create a follow-up task,
        or when a situation requires human intervention.
        Query format: 'escalate ticket TKT-001 reason: pickup delay exceeds SLA'
        Always prepare first — confirmation is required before the escalation is created.
        """
        import re

        ticket_match = re.search(r"tkt-(\d+)", query.lower())
        order_match = re.search(r"ord-(\d+)", query.lower())
        
        reason_match = re.search(r"reason[:\s]+(.+)", query.lower())
        reason = reason_match.group(1).strip() if reason_match else "Not specified"

        ref_id = None
        ref_type = None

        if ticket_match:
            ref_id = f"TKT-{ticket_match.group(1)}"
            ref_type = "ticket"
        elif order_match:
            ref_id = f"ORD-{order_match.group(1)}"
            ref_type = "order"

        if not ref_id:
            return "PREPARE_ESCALATION_FAILED: Could not identify a ticket or order ID in the request."

        escalation_preview = {
            "ref_id": ref_id,
            "ref_type": ref_type,
            "reason": reason,
            "account_id": account_id,
            "role": role,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PENDING_CONFIRMATION"
        }

        preview_text = (
            f"ESCALATION_READY_FOR_CONFIRMATION\n"
            f"Reference: {ref_id} ({ref_type})\n"
            f"Reason: {reason}\n"
            f"Account: {account_id or 'Internal'}\n"
            f"Raised by: {role}\n"
            f"Time: {escalation_preview['timestamp']}\n\n"
            f"Please confirm to proceed with this escalation."
        )

        return preview_text

    return prepare_escalation


def confirm_escalation(ref_id, ref_type, reason, account_id, role):
    escalation = {
        "escalation_id": f"ESC-{len(ESCALATION_STORE) + 1001}",
        "ref_id": ref_id,
        "ref_type": ref_type,
        "reason": reason,
        "account_id": account_id,
        "raised_by": role,
        "status": "OPEN",
        "created_at": datetime.utcnow().isoformat()
    }
    ESCALATION_STORE.append(escalation)
    return escalation


def get_all_escalations():
    return ESCALATION_STORE