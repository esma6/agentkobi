from __future__ import annotations

import os
from typing import Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
from app.models.tools import get_orders_by_status

class CustomerSummary(BaseModel):
    active_customers_yesterday: int = Field(description="Dün sipariş veren aktif müşteri sayısı")
    top_customer_name: str = Field(description="En çok sipariş veren müşterinin adı")

async def run(business_id: str) -> dict[str, Any]:
    """Müşteri durumunu özetleyen LLM ajanı."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY tanımlı değil")

    model = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.1,
    )
    
    tools = [get_orders_by_status]
    llm_with_tools = llm.bind_tools(tools)
    llm_structured = llm.with_structured_output(CustomerSummary)
    
    prompt = f"""
    Sen AgentKobi'nin müşteri ilişkileri ajanısın.
    Görevin, sipariş verilerini inceleyerek müşteri hareketliliğini özetlemektir.
    
    Sana verilen araçları (tools) kullanarak:
    1. Son siparişlerde en çok görünen müşteriyi (veya dün sipariş verenleri) bulmaya çalış.
    2. Aktif müşteri sayısını tahmin et.
    
    Mutlaka araçları kullanarak verileri çek.
    """
    
    messages: list[Any] = [("human", prompt)]
    response = await llm_with_tools.ainvoke(messages)
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name == "get_orders_by_status":
                result = get_orders_by_status.invoke(tool_args)
                messages.append(response)
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                
                final_response = await llm_structured.ainvoke(messages)
                return final_response.model_dump()
                
    return {"active_customers_yesterday": 0, "top_customer_name": "Bilinmiyor"}

