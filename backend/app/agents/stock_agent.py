from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from langchain_core.messages import ToolMessage
from app.agents.llm_provider import get_llm
from app.models.tools import get_critical_stock

class StockAlert(BaseModel):
    product_id: str
    sku: str
    product_name: str
    current_quantity: float
    reorder_threshold: float
    missing_quantity: float
    unit: str

class StockAlerts(BaseModel):
    alerts: list[StockAlert]

async def run(business_id: str) -> list[dict[str, Any]]:
    """Stok durumunu özetleyen LLM ajanı."""
    llm = get_llm(temperature=0.1)
    
    tools = [get_critical_stock]
    llm_with_tools = llm.bind_tools(tools)
    llm_structured = llm.with_structured_output(StockAlerts)
    
    prompt = f"""
    Sen AgentKobi'nin stok takip ajanısın.
    Görevin, kritik stok seviyesinin altına düşen ürünleri tespit etmektir.
    
    Sana verilen araçları (tools) kullanarak kritik stoktaki ürünleri bul.
    Her ürün için:
    - product_id (id alanından)
    - sku
    - product_name (name alanından)
    - current_quantity (stock_quantity alanından)
    - reorder_threshold
    - missing_quantity (eksik_miktar alanından)
    - unit
    bilgilerini içeren bir liste oluştur.
    
    Mutlaka araçları kullanarak verileri çek.
    """
    
    messages: list[Any] = [("human", prompt)]
    response = await llm_with_tools.ainvoke(messages)
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name == "get_critical_stock":
                result = get_critical_stock.invoke(tool_args)
                messages.append(response)
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                
                final_response = await llm_structured.ainvoke(messages)
                return final_response.model_dump()["alerts"]
                
    return []


