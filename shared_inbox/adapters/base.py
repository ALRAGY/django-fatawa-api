import importlib
import pkgutil
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BasePlatformAdapter:
    """
    الواجهة الأساسية (Interface) لكل محركات المنصات.
    أي منصة جديدة سيتم إضافتها يجب أن ترث من هذا الكلاس وتقوم ببرمجة الدوال فيه.
    """
    platform_identifier = None  # e.g., 'YOUTUBE', 'FACEBOOK'
    requires_polling = False    # True if the platform uses Polling (API requests intervals)

    def __init__(self, channel):
        """
        :param channel: نسخة من مودل ConnectedChannel للوصول إلى credentials.
        """
        self.channel = channel
        self.credentials = channel.credentials

    def fetch_messages(self):
        """
        للمنصات التي لا تدعم Webhooks وتتطلب جلب دوري (Polling).
        """
        if not self.requires_polling:
            raise NotImplementedError("هذه المنصة لا تتطلب جلب دوري، تعمل عن طريق الـ Webhook.")
        pass

    def process_webhook(self, payload: Dict[str, Any]):
        """
        لمعالجة الـ Webhooks الواردة للمنصات الفورية.
        """
        pass

    def reply(self, external_message_id: str, text: str) -> bool:
        """
        كيفية الرد على رسالة أو تعليق باستخدام API المنصة.
        """
        raise NotImplementedError("يجب على المحرك تعريف طريقة الرد لهذه المنصة.")

    def delete(self, external_message_id: str) -> bool:
        """
        كيفية حذف رسالة أو تعليق من المنصة وتحديثها في جانغو.
        """
        raise NotImplementedError("يجب على المحرك تعريف طريقة الحذف لهذه المنصة.")


class PlatformRegistry:
    """
    نظام ديناميكي يكتشف ويُسجل جميع المحركات بشكل آلي من مجلد (adapters).
    """
    _registry = {}

    @classmethod
    def register(cls, adapter_class):
        if not adapter_class.platform_identifier:
            raise ValueError(f"المحرك {adapter_class.__name__} لا يملك platform_identifier.")
        cls._registry[adapter_class.platform_identifier] = adapter_class
        logger.info(f"تم تسجيل محرك منصة: {adapter_class.platform_identifier}")
        return adapter_class

    @classmethod
    def get_adapter_class(cls, platform_identifier: str):
        adapter_class = cls._registry.get(platform_identifier)
        if not adapter_class:
            raise ValueError(f"المحرك للمنصة {platform_identifier} غير مسجل في النظام.")
        return adapter_class

    @classmethod
    def load_all_adapters(cls):
        """
        ينسخ هذا الكود جميع الملفات داخل مجلد adapters ويستدعيها لتشغيل الـ @register.
        """
        import shared_inbox.adapters
        for _, module_name, _ in pkgutil.iter_modules(shared_inbox.adapters.__path__):
            if module_name != 'base':
                try:
                    importlib.import_module(f'shared_inbox.adapters.{module_name}')
                except Exception as e:
                    logger.error(f"فشل في تحميل المحرك {module_name}: {e}")


