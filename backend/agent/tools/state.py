from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    account_id: Optional[str]
    role: str
    tool_trace: List[dict]
    pending_action: Optional[dict]
    awaiting_confirmation: bool