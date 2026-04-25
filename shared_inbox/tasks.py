from celery import shared_task
import logging
from .models import ConnectedChannel
from .adapters.base import PlatformRegistry

logger = logging.getLogger(__name__)

@shared_task
def fetch_all_polling_channels():
    """
    مهمة خلفية تدور على كل القنوات المربوطة لتشغيل عملية السحب للمنصات التي تعتمد على الـ Polling.
    """
    logger.info("Starting background fetching for all connected channels...")
    active_channels = ConnectedChannel.objects.filter(is_active=True)

    for channel in active_channels:
        try:
            adapter_class = PlatformRegistry.get_adapter_class(channel.platform_identifier)
            # Only poll if the platform requires it natively
            if adapter_class.requires_polling:
                logger.info(f"Polling channel: {channel.name} ({channel.platform_identifier})")
                adapter = adapter_class(channel=channel)
                adapter.fetch_messages()
        except ValueError as e:
            logger.error(f"Error loading adapter for {channel.name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching channel {channel.name}: {e}")

    logger.info("Finished background fetching cycle.")
