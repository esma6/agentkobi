from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from langchain_core.messages import ToolMessage
from app.agents.llm_provider import get_llm
from app.models.tools import get_daily_summary, get_orders_by_status

class OrderSummary(BaseModel):
    new_orders_yesterday: int = Field(description="Dün gelen yeni sipariş sayısı")
    pending_to_prepare_today: int = Field(description="Bugün hazırlanması bekleyen sipariş sayısı")
    ready_to_ship_today: int = Field(description="Bugün kargoya verilmeyi bekleyen sipariş sayısı")

async def run(business_id: str) -> dict[str, Any]:
    """Sipariş durumunu özetleyen LLM ajanı."""
    llm = get_llm(temperature=0.1)
    
    tools = [get_daily_summary, get_orders_by_status]
    llm_with_tools = llm.bind_tools(tools)
    llm_structured = llm.with_structured_output(OrderSummary)
    
    prompt = f"""
    Sen AgentKobi'nin sipariş takip ajanısın. 
    Görevin, sabah brifingi için sipariş sayılarını çıkarmaktır.
    
    Sana verilen araçları (tools) kullanarak aşağıdaki bilgileri bul:
    1. Dün (bir önceki gün) gelen yeni sipariş sayısı.
    2. Durumu 'confirmed' olan (hazırlanması bekleyen) sipariş sayısı.
    3. Durumu 'preparing' olan (kargoya hazır) sipariş sayısı.
    
    Mutlaka araçları kullanarak verileri çek.
    """
    
    messages: list[Any] = [("human", prompt)]
    response = await llm_with_tools.ainvoke(messages)
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name == "get_daily_summary":
                result = get_daily_summary.invoke(tool_args)
            elif tool_name == "get_orders_by_status":
                result = get_orders_by_status.invoke(tool_args)
            else:
                result = "Tool not found"
                
            messages.append(response)
            messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
            
        final_response = await llm_structured.ainvoke(messages)
        return final_response.model_dump()
        
    return {
        "new_orders_yesterday": 0,
        "pending_to_prepare_today": 0,
        "ready_to_ship_today": 0,
    }


