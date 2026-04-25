from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Question(models.Model):
    """
    نموذج وهمي للأسئلة كما طُلب في الخطة.
    """
    title = models.CharField(max_length=255, verbose_name=_("عنوان السؤال"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ConnectedChannel(models.Model):
    """
    جدول يمثل الحسابات أو القنوات المربوطة بالنظام (مثلاً: صفحة فيسبوك 1، قناة يوتيوب المختصة، رقم واتساب 1)
    """
    class PlatformType(models.TextChoices):
        YOUTUBE = 'YOUTUBE', _('يوتيوب (YouTube)')
        FACEBOOK = 'FACEBOOK', _('فيسبوك (Facebook)')
        INSTAGRAM = 'INSTAGRAM', _('انستغرام (Instagram)')
        TIKTOK = 'TIKTOK', _('تيك توك (TikTok)')
        WHATSAPP = 'WHATSAPP', _('واتساب (WhatsApp)')
        TELEGRAM = 'TELEGRAM', _('تيليجرام (Telegram)')
        OTHER = 'OTHER', _('أخرى (Other)')

    name = models.CharField(max_length=255, verbose_name=_("اسم القناة/الصفحة"))
    platform_identifier = models.CharField(
        max_length=50, 
        choices=PlatformType.choices, 
        verbose_name=_("نوع المنصة")
    )
    # JSONField to store tokens, api keys, page_id, etc.
    credentials = models.JSONField(default=dict, blank=True, verbose_name=_("بيانات الربط السرية (Credentials)"))
    is_active = models.BooleanField(default=True, verbose_name=_("نشط"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("قناة تواصل")
        verbose_name_plural = _("قنوات التواصل المتصلة")

    def __str__(self):
        return f"{self.name} ({self.get_platform_identifier_display()})"


class IncomingMessage(models.Model):
    class ProcessStatus(models.TextChoices):
        PENDING = 'PENDING', _('قيد الانتظار')
        FORWARDED = 'FORWARDED', _('تم التحويل')
        REPLIED = 'REPLIED', _('تم الرد')
        DELETED = 'DELETED', _('محذوف')

    class MessageType(models.TextChoices):
        COMMENT = 'COMMENT', _('تعليق (Comment)')
        DIRECT_MESSAGE = 'DIRECT_MESSAGE', _('رسالة خاصة (DM)')
        MENTION = 'MENTION', _('إشارة (Mention)')

    channel = models.ForeignKey(
        ConnectedChannel,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("القناة المتصلة"),
        null=True, blank=True # temporary null for migration compatibility
    )
    message_type = models.CharField(
        max_length=50, 
        choices=MessageType.choices, 
        default=MessageType.DIRECT_MESSAGE,
        verbose_name=_("نوع الرسالة")
    )
    
    # المعرفات المطلوبة للمنصات الخارجية للرد والحذف
    external_message_id = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("معرف الرسالة الخارجي"))
    external_parent_id = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("معرف المنشور/الفيديو الخارجي"))

    message_content = models.TextField(verbose_name=_("نص الرسالة الأصلي"))
    sender_identifier = models.CharField(max_length=255, verbose_name=_("معرف المرسل"))
    attachment_url = models.TextField(null=True, blank=True, verbose_name=_("رابط المرفقات"))
    
    process_status = models.CharField(
        max_length=30,
        choices=ProcessStatus.choices,
        default=ProcessStatus.PENDING,
        verbose_name=_("حالة المعالجة")
    )
    reply_content = models.TextField(null=True, blank=True, verbose_name=_("نص الرد"))
    action_taken_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inbox_actions",
        verbose_name=_("متخذ القرار")
    )
    target_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_messages",
        verbose_name=_("السؤال المرتبط")
    )
    internal_notes = models.TextField(null=True, blank=True, verbose_name=_("ملاحظات داخلية"))
    received_at = models.DateTimeField(auto_now_add=True, verbose_name=_("وقت الوصول"))
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("وقت المعالجة"))

    class Meta:
        ordering = ['-received_at']
        verbose_name = _('رسالة واردة')
        verbose_name_plural = _('الرسائل الواردة')

    def __str__(self):
        try:
            return f"[{self.channel.name}] {self.get_message_type_display()} - {self.sender_identifier}"
        except AttributeError:
            return f"Message - {self.sender_identifier}"
