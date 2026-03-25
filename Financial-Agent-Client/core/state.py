"""Global state contract for the multi-agent investment workflow."""

import operator
from typing import Annotated, Literal, Sequence, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """Shared graph state with reducer-friendly fields for fan-out/fan-in."""

    messages: Annotated[Sequence[BaseMessage], operator.add]
    research_intent: Literal["fundamental", "sentiment", "comprehensive", "unknown"]
    historical_context: Annotated[list[str], operator.add]
    realtime_news: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
