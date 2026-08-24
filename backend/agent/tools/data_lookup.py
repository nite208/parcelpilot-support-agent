import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain.tools import tool
from db.queries import (
    get_order, get_order_internal, get_orders_for_account,
    get_ticket, get_tickets_for_account, get_all_open_tickets,
    get_all_orders, get_account, get_account_by_order,
    search_tickets_by_keyword
)


def build_data_lookup_tool(account_id=None, role="customer"):

    @tool
    def data_lookup(query: str) -> str:
        """
        Look up structured data including orders, tickets, and account information.
        Use this to find order status, shipment details, ticket history, and account plan.
        Query examples: 'order ORD-1001', 'tickets for account', 'ticket TKT-005',
        'all open tickets', 'account details', 'orders with status BOOKED'.
        """
        query_lower = query.lower()

        if any(x in query_lower for x in ["order ", "ord-"]):
            order_id = None
            for word in query.upper().split():
                if word.startswith("ORD-") or (word.isdigit() and len(word) > 2):
                    order_id = word if word.startswith("ORD-") else f"ORD-{word}"
                    break
            
            if order_id:
                if role == "internal":
                    order = get_order_internal(order_id)
                    if order:
                        account = get_account_by_order(order_id)
                        result = f"Order: {dict(order)}"
                        if account:
                            result += f"\nAccount: {dict(account)}"
                        return result
                    return f"Order {order_id} not found."
                else:
                    order = get_order(order_id, account_id)
                    if order:
                        return f"Order: {dict(order)}"
                    return f"Order {order_id} not found or does not belong to your account."
            
            if "all" in query_lower or "list" in query_lower:
                if role == "internal":
                    orders = get_all_orders()
                    if not orders:
                        return "No orders found."
                    return "\n".join([str(o) for o in orders[:20]])
                else:
                    orders = get_orders_for_account(account_id)
                    if not orders:
                        return "No orders found for your account."
                    return "\n".join([str(o) for o in orders])

        if any(x in query_lower for x in ["ticket", "tkt-"]):
            ticket_id = None
            for word in query.upper().split():
                if word.startswith("TKT-"):
                    ticket_id = word
                    break
            
            if ticket_id:
                if role == "internal":
                    ticket = get_ticket(ticket_id)
                else:
                    ticket = get_ticket(ticket_id, account_id)
                
                if ticket:
                    return f"Ticket: {dict(ticket)}"
                return f"Ticket {ticket_id} not found or access denied."
            
            if "all open" in query_lower or "open tickets" in query_lower:
                if role == "internal":
                    tickets = get_all_open_tickets()
                    if not tickets:
                        return "No open tickets."
                    return "\n".join([str(t) for t in tickets])
                else:
                    tickets = get_tickets_for_account(account_id)
                    open_tickets = [t for t in tickets if t.get("status") != "CLOSED"]
                    if not open_tickets:
                        return "No open tickets for your account."
                    return "\n".join([str(t) for t in open_tickets])
            
            if role == "internal" and ("search" in query_lower or "keyword" in query_lower):
                words = query.split()
                keyword = words[-1] if len(words) > 1 else ""
                tickets = search_tickets_by_keyword(keyword)
                if not tickets:
                    return f"No tickets found matching '{keyword}'."
                return "\n".join([str(t) for t in tickets])
            
            if role == "internal":
                tickets = get_all_open_tickets()
            else:
                tickets = get_tickets_for_account(account_id)
            
            if not tickets:
                return "No tickets found."
            return "\n".join([str(t) for t in tickets])

        if any(x in query_lower for x in ["account", "plan", "acct-"]):
            if role == "internal":
                acct_id = None
                for word in query.upper().split():
                    if word.startswith("ACCT-"):
                        acct_id = word
                        break
                if acct_id:
                    account = get_account(acct_id)
                    if account:
                        return f"Account: {dict(account)}"
                    return f"Account {acct_id} not found."
                return "Please specify an account ID for internal lookup."
            else:
                account = get_account(account_id)
                if account:
                    return f"Account: {dict(account)}"
                return "Account details not found."

        return "Could not parse the data lookup query. Try specifying an order ID (ORD-XXXX), ticket ID (TKT-XXXX), or account details."

    return data_lookup