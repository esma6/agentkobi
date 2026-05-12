import os
import httpx
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")

logger = logging.getLogger(__name__)

load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")




async def send_telegram_message(message: str) -> bool:
    """Telegram botu üzerinden mesaj gönderir."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token veya Chat ID tanımlı değil. Mesaj gönderilemedi.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                print("Telegram mesajı başarıyla gönderildi.")
                return True
            else:
                print(f"Telegram API hatası: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Telegram mesajı gönderilirken hata oluştu: {e}")
        return False

