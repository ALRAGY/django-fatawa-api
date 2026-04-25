import logging
from typing import Dict, Any, Optional
from shared_inbox.models import IncomingMessage

logger = logging.getLogger(__name__)

class WebhookNormalizer:
    """Base class for normalizing incoming webhook payloads."""
    
    @classmethod
    def normalize(cls, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        raise NotImplementedError("Subclasses must implement the normalize method.")


class WhatsAppNormalizer(WebhookNormalizer):
    """
    Normalizes WhatsApp webhook payloads.
    Assumes a standard Meta/Twilio WhatsApp payload layout.
    """
    @classmethod
    def normalize(cls, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        try:
            # Example standard layout parsing - depends on actual provider (Twilio, Cloud API)
            # Defaulting to a simplistic generic check for WhatsApp
            sender_identifier = payload.get("From", payload.get("sender", "Unknown"))
            message_content = payload.get("Body", payload.get("message", ""))
            attachment_url = payload.get("MediaUrl0", None) # Twilio format example
            
            message = IncomingMessage.objects.create(
                source_platform=IncomingMessage.SourcePlatform.WHATSAPP,
                message_content=message_content,
                sender_identifier=sender_identifier,
                attachment_url=attachment_url
            )
            return message
        except Exception as e:
            logger.error(f"WhatsAppNormalizer error: {e}")
            raise ValueError(f"Invalid WhatsApp payload: {e}")


class TelegramNormalizer(WebhookNormalizer):
    """
    Normalizes Telegram webhook payloads.
    """
    @classmethod
    def normalize(cls, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        try:
            # Standard Telegram Bot API payload
            message_data = payload.get("message", {})
            chat = message_data.get("chat", {})
            sender_identifier = str(chat.get("id", "Unknown"))
            
            message_content = message_data.get("text", "")
            
            attachment_url = None
            if "photo" in message_data:
                # Store placeholder or highest resolution photo id
                attachment_url = f"telegram_photo_id_{message_data['photo'][-1]['file_id']}"
            elif "document" in message_data:
                attachment_url = f"telegram_doc_id_{message_data['document']['file_id']}"

            message = IncomingMessage.objects.create(
                source_platform=IncomingMessage.SourcePlatform.TELEGRAM,
                message_content=message_content,
                sender_identifier=sender_identifier,
                attachment_url=attachment_url
            )
            return message
        except Exception as e:
            logger.error(f"TelegramNormalizer error: {e}")
            raise ValueError(f"Invalid Telegram payload: {e}")


def process_webhook(platform: str, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
    """
    Main entry point for the views. Routes to the correct Normalizer.
    """
    platform = platform.upper()
    
    if platform == 'WHATSAPP':
        return WhatsAppNormalizer.normalize(payload)
    elif platform == 'TELEGRAM':
        return TelegramNormalizer.normalize(payload)
    else:
        # Generic / Other normalizer
        sender = payload.get('sender', 'Unknown')
        content = payload.get('content', str(payload))
        message = IncomingMessage.objects.create(
            source_platform=IncomingMessage.SourcePlatform.OTHER,
            message_content=content,
            sender_identifier=sender
        )
        return message
