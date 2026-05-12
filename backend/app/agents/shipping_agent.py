from __future__ import annotations

import os
from typing import Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
from app.models.tools import get_daily_summary, get_delayed_shipments, get_orders_by_status

class DelayedOrder(BaseModel):
    order_number: int
    customer_name: str = ""
    customer_phone: str = ""
    tracking_number: str = ""
    estimated_delivery: str = ""

class ShippingSummary(BaseModel):
    to_ship: int = Field(description="Kargoya verilmeyi bekleyen sipariş sayısı")
    in_transit: int = Field(description="Yolda olan sipariş sayısı")
    delayed: int = Field(description="Gecikmiş kargo sayısı")
    delayed_orders: list[DelayedOrder] = Field(description="Gecikmiş siparişlerin listesi")

async def run(business_id: str) -> dict[str, Any]:
    """Kargo durumunu özetleyen LLM ajanı."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY tanımlı değil")

    model = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.1,
    )
    
    tools = [get_daily_summary, get_delayed_shipments, get_orders_by_status]
    llm_with_tools = llm.bind_tools(tools)
    llm_structured = llm.with_structured_output(ShippingSummary)
    
    prompt = f"""
    Sen AgentKobi'nin kargo takip ajanısın.
    Görevin, kargoya verilecek, yolda olan ve gecikmiş kargoların sayısını ve detaylarını bulmaktır.
    
    Sana verilen araçları (tools) kullanarak aşağıdaki bilgileri bul:
    1. Kargoya verilmeyi bekleyen (ready to ship / status: preparing) sipariş sayısı.
    2. Yolda olan (status: shipped) sipariş sayısı.
    3. Gecikmiş veya şubede bekleyen kargo sayısı ve bu siparişlerin listesi.
    
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
            elif tool_name == "get_delayed_shipments":
                result = get_delayed_shipments.invoke(tool_args)
            elif tool_name == "get_orders_by_status":
                result = get_orders_by_status.invoke(tool_args)
            else:
                result = "Tool not found"
                
            messages.append(response)
            messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
            
        final_response = await llm_structured.ainvoke(messages)
        return final_response.model_dump()
        
    return {"to_ship": 0, "in_transit": 0, "delayed": 0, "delayed_orders": []}


