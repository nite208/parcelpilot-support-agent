import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agent.state import AgentState
from agent.tools.document_search import build_document_search_tool
from agent.tools.data_lookup import build_data_lookup_tool
from agent.tools.escalation import build_escalation_tool
from config import GROQ_API_KEY


CUSTOMER_SYSTEM_PROMPT = """You are a helpful customer support agent for ParcelPilot, a logistics platform.

The authenticated customer's account ID is already known from their login session — do not ask them for it.
You have direct access to their account data through the data_lookup tool.

You help customers with questions about their shipments, support policies, cancellations, and service credits.

Rules you must follow:
- Only answer using information from the tools provided. Do not invent answers.
- Always check if the customer has a signed agreement that overrides default policy. Customer agreements take highest priority.
- Never share data from other accounts. You only have access to this customer's data.
- If a document source is marked DEPRECATED, ignore it and say so explicitly.
- If sources conflict, state the conflict clearly and apply the highest-authority source.
- For cancellation fees, service credits, or SLA questions — always check the customer agreement first, then the current SOP.
- Before creating an escalation or any action, prepare it and ask the user to confirm.
- If you cannot answer with confidence, escalate to the support team rather than guessing.
- Be concise and clear. Do not repeat the same information multiple times."""


INTERNAL_SYSTEM_PROMPT = """You are an internal support operations assistant for ParcelPilot staff.

You have access to all account data, orders, tickets, and policy documents.

Rules you must follow:
- Use the tools to retrieve accurate data before answering.
- Customer agreements override default policy. Always check for a customer-specific agreement.
- Historical ticket resolutions may be incorrect. Treat them as context only.
- If a document source is marked DEPRECATED, flag it explicitly and use the current version instead.
- For any state-changing action, prepare it first and require explicit confirmation before executing.
- When sources conflict, surface the conflict clearly and identify which source takes priority.
- You may access data across all accounts. Use this responsibly.
- Proactively flag SLA breaches, unusual patterns, or issues that need attention."""


def build_agent(account_id=None, role="customer"):
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="openai/gpt-oss-20b",
        temperature=0
    )

    tools = [
        build_document_search_tool(account_id=account_id, role=role),
        build_data_lookup_tool(account_id=account_id, role=role),
        build_escalation_tool(account_id=account_id, role=role)
    ]

    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    system_prompt = CUSTOMER_SYSTEM_PROMPT if role == "customer" else INTERNAL_SYSTEM_PROMPT

    def call_llm(state: AgentState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + list(messages)
        
        response = llm_with_tools.invoke(messages)
        
        tool_trace = state.get("tool_trace", [])
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_trace.append({
                    "tool": tc["name"],
                    "input": tc["args"]
                })
        
        return {
            "messages": [response],
            "tool_trace": tool_trace
        }

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")

    return graph.compile()


def run_agent(message, history, account_id=None, role="customer"):
    agent = build_agent(account_id=account_id, role=role)

    system_prompt = CUSTOMER_SYSTEM_PROMPT if role == "customer" else INTERNAL_SYSTEM_PROMPT
    messages = [SystemMessage(content=system_prompt)]

    for h in history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        elif h["role"] == "assistant":
            messages.append(AIMessage(content=h["content"]))

    messages.append(HumanMessage(content=message))

    state = {
        "messages": messages,
        "account_id": account_id,
        "role": role,
        "tool_trace": [],
        "pending_action": None,
        "awaiting_confirmation": False
    }

    result = agent.invoke(state)

    last_message = result["messages"][-1]
    response_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    return {
        "response": response_text,
        "tool_trace": result.get("tool_trace", [])
    }