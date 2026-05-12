import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")

logger = logging.getLogger(__name__)


def _send_email_sync(subject: str, body: str, to_email: str) -> bool:
    """Senkron e-posta gönderimi (arka planda çalıştırılacak)."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = os.getenv("SMTP_FROM", smtp_user)
    
    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.warning("SMTP ayarları eksik. E-posta gönderilemedi.")
        return False
        
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    
    msg.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        logger.info(f"E-posta başarıyla gönderildi: {to_email}")
        return True
    except Exception as e:
        logger.error(f"E-posta gönderilirken hata oluştu: {e}")
        return False

async def send_email(subject: str, body: str, to_email: str) -> bool:
    """Asenkron e-posta gönderimi (event loop'u bloklamaz)."""
    return await asyncio.to_thread(_send_email_sync, subject, body, to_email)
