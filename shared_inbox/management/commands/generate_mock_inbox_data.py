from django.core.management.base import BaseCommand
from shared_inbox.models import IncomingMessage, Question
from accounts.models import User
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Generates dummy data for the Shared Inbox (Questions and IncomingMessages)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Checking Users...")
        # Get or create a fallback user for actions
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_staff=True).first()
        
        self.stdout.write("Clearing existing mock data...")
        IncomingMessage.objects.all().delete()
        Question.objects.all().delete()

        self.stdout.write("Creating mock questions...")
        q1 = Question.objects.create(title="ما حكم الصيام في السفر؟ (تجريبي)")
        q2 = Question.objects.create(title="كيف أزكي عن مالي؟ (تجريبي)")

        self.stdout.write("Creating mock incoming messages...")
        
        # 1. Pending WhatsApp Message
        IncomingMessage.objects.create(
            source_platform=IncomingMessage.SourcePlatform.WHATSAPP,
            message_content="السلام عليكم، أريد الاستفسار عن كفارة اليمين.",
            sender_identifier="+966501234567",
            process_status=IncomingMessage.ProcessStatus.PENDING
        )

        # 2. Forwarded Telegram Message
        IncomingMessage.objects.create(
            source_platform=IncomingMessage.SourcePlatform.TELEGRAM,
            message_content="هل يجوز المسح على الجوارب؟",
            sender_identifier="user123_tg",
            process_status=IncomingMessage.ProcessStatus.FORWARDED,
            target_question=q1,
            internal_notes="تم التحويل للقسم المختص."
        )

        # 3. Replied WhatsApp Message (with attachment link)
        IncomingMessage.objects.create(
            source_platform=IncomingMessage.SourcePlatform.WHATSAPP,
            message_content="ما هو نصاب زكاة الذهب؟ (مرفق صورة)",
            sender_identifier="+966509876543",
            attachment_url="https://example.com/media/gold.jpg",
            process_status=IncomingMessage.ProcessStatus.REPLIED,
            reply_content="نصاب الذهب 85 جراماً.",
            target_question=q2,
            action_taken_by=admin_user,
            processed_at=timezone.now()
        )

        # 4. Other Platform Message
        IncomingMessage.objects.create(
            source_platform=IncomingMessage.SourcePlatform.OTHER,
            message_content="استفسار عام عن أوقات العمل.",
            sender_identifier="email@example.com",
            process_status=IncomingMessage.ProcessStatus.DELETED,
            internal_notes="رسالة غير متعلقة بالفتاوى."
        )

        self.stdout.write(self.style.SUCCESS("Successfully generated mock Shared Inbox data!"))
