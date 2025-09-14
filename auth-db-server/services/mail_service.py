import os
from services.base import handle_service_errors
from typing import Dict, Optional, Tuple
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils.logging_config import get_logger

logger = get_logger('services.mail_service')

@handle_service_errors("Send mail")
def send_mail(to_email: str, subject: str, html_content: str) -> Tuple[Optional[int], Optional[str], Optional[Dict]]:
    message = Mail(
        from_email=os.getenv('SENDGRID_FROM_EMAIL'),
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        return True, None
    except Exception as e:
        return False, e.message
