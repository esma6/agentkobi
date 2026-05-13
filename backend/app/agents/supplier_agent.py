from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from langchain_core.messages import ToolMessage
from app.agents.llm_provider import get_llm
from app.models.tools import get_pending_drafts

class SupplierDraft(BaseModel):
    id: str
    product_id: str = ""
    supplier_name: str = ""
    subject: str = ""
    suggested_quantity: float = 0.0
    estimated_cost: float = 0.0
    status: str = ""

class SupplierDrafts(BaseModel):
    drafts: list[SupplierDraft]

async def run(business_id: str) -> list[dict[str, Any]]:
    """Tedarikçi taslaklarını özetleyen LLM ajanı."""
    llm = get_llm(temperature=0.1)
    
    tools = [get_pending_drafts]
    llm_with_tools = llm.bind_tools(tools)
    llm_structured = llm.with_structured_output(SupplierDrafts)
    
    prompt = f"""
    Sen AgentKobi'nin tedarik takip ajanısın.
    Görevin, onay bekleyen tedarikçi sipariş taslaklarını bulmaktır.
    
    Sana verilen araçları (tools) kullanarak onay bekleyen (status: pending) taslakları bul.
    
    Mutlaka araçları kullanarak verileri çek.
    """
    
    messages: list[Any] = [("human", prompt)]
    response = await llm_with_tools.ainvoke(messages)
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name == "get_pending_drafts":
                result = get_pending_drafts.invoke(tool_args)
                messages.append(response)
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                
                final_response = await llm_structured.ainvoke(messages)
                return final_response.model_dump()["drafts"]
                
    return []


