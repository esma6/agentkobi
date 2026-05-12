import asyncio
from app.core.celery import celery_app
from app.graph.orchestrator import run_workflow
from app.core.telegram import send_telegram_message
from app.core.email import send_email
import logging
import os

logger = logging.getLogger(__name__)

@celery_app.task
def send_morning_briefing_task():
    """Sabah brifingini üreten ve gönderen Celery görevi."""
    logger.info("Sabah brifingi görevi başladı.")
    
    business_id = os.getenv("DEFAULT_BUSINESS_ID", "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    
    async def _run():
        result = await run_workflow(business_id)
        briefing = result.get("briefing_final", "Brifing üretilemedi.")
        
        # Telegram Gönderimi
        await send_telegram_message(briefing)
        
        # E-posta Gönderimi
        target_email = os.getenv("BRIEFING_EMAIL")
        if target_email:
            await send_email("Günlük Sabah Brifingi", briefing, target_email)
            
        return "Success"

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error(f"Sabah brifingi görevinde hata: {e}")
        return f"Error: {e}"
