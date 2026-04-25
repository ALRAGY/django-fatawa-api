from .base import BasePlatformAdapter, PlatformRegistry
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.utils import timezone
from shared_inbox.models import IncomingMessage

logger = logging.getLogger(__name__)

@PlatformRegistry.register
class YouTubeAdapter(BasePlatformAdapter):
    platform_identifier = 'YOUTUBE'
    requires_polling = True

    def _get_service(self):
        """Constructs and returns the YouTube API service object."""
        # credentials dict from ConnectedChannel
        creds = Credentials(
            token=self.credentials.get("access_token"),
            refresh_token=self.credentials.get("refresh_token"),
            token_uri=self.credentials.get("token_uri"),
            client_id=self.credentials.get("client_id"),
            client_secret=self.credentials.get("client_secret")
        )
        return build('youtube', 'v3', credentials=creds, cache_discovery=False)

    def _get_channel_id(self, youtube):
        """Fetches the user's own channel ID if not stored in credentials."""
        if "channel_id" in self.credentials:
            return self.credentials["channel_id"]
            
        request = youtube.channels().list(mine=True, part="id")
        response = request.execute()
        if response.get("items"):
            channel_id = response["items"][0]["id"]
            # Cache it in the DB to avoid redundant API calls
            self.channel.credentials["channel_id"] = channel_id
            self.channel.save()
            return channel_id
        return None

    def fetch_messages(self):
        """يستخدم الجلب الدوري للبحث عن التعليقات الجديدة في القناة بالكامل"""
        logger.info(f"جلب التعليقات من قناة يوتيوب: {self.channel.name}")
        try:
            youtube = self._get_service()
            channel_id = self._get_channel_id(youtube)
            
            if not channel_id:
                logger.error("لم يتم العثور على قناة متعلقة بهذا الحساب.")
                return

            request = youtube.commentThreads().list(
                allThreadsRelatedToChannelId=channel_id,
                part="snippet,replies",
                maxResults=20, # الجلب الأحدث فقط في كل مرة
                order="time"
            )
            response = request.execute()

            for item in response.get("items", []):
                top_comment = item["snippet"]["topLevelComment"]
                comment_id = top_comment["id"]
                snippet = top_comment["snippet"]
                
                video_id = snippet.get("videoId", "")
                text = snippet.get("textOriginal", "")
                author = snippet.get("authorDisplayName", "Unknown")
                
                # Check if it already exists
                if not IncomingMessage.objects.filter(external_message_id=comment_id).exists():
                    IncomingMessage.objects.create(
                        channel=self.channel,
                        message_type=IncomingMessage.MessageType.COMMENT,
                        external_message_id=comment_id,
                        external_parent_id=video_id,
                        message_content=text,
                        sender_identifier=author
                    )
            logger.info("اكتمل سحب تعليقات اليوتيوب بنجاح.")
        except Exception as e:
            logger.error(f"خطأ أثناء سحب تعليقات اليوتيوب: {e}")

    def reply(self, external_message_id: str, text: str) -> bool:
        """الرد المباشر على التعليق من داخل نظام جانغو"""
        logger.info(f"الرد على يوتيوب {external_message_id}: {text}")
        try:
            youtube = self._get_service()
            request = youtube.comments().insert(
                part="snippet",
                body={
                    "snippet": {
                        "parentId": external_message_id,
                        "textOriginal": text
                    }
                }
            )
            request.execute()
            
            # تحديث حالة الرسالة في جانغو
            msg = IncomingMessage.objects.get(external_message_id=external_message_id)
            msg.process_status = IncomingMessage.ProcessStatus.REPLIED
            msg.reply_content = text
            msg.processed_at = timezone.now()
            msg.save()
            return True
        except Exception as e:
            logger.error(f"فشل الرد على يوتيوب: {e}")
            raise e

    def delete(self, external_message_id: str) -> bool:
        """يستخدم API يوتيوب لحذف التعليق نهائياً بناءً على إذن صاحب القناة"""
        logger.info(f"حذف تعليق يوتيوب: {external_message_id}")
        try:
            youtube = self._get_service()
            request = youtube.comments().setModerationStatus(id=external_message_id, moderationStatus="rejected")
            # Or if it's the user's own comment: youtube.comments().delete(id=external_message_id) 
            # We will use setModerationStatus to hide it, which acts as a delete for audience, 
            # because comments().delete() only works for comments authored by the authenticated user himself.
            request.execute()
            
            # تحديث حالة الرسالة في جانغو
            msg = IncomingMessage.objects.get(external_message_id=external_message_id)
            msg.process_status = IncomingMessage.ProcessStatus.DELETED
            msg.processed_at = timezone.now()
            msg.save()
            return True
        except Exception as e:
            logger.error(f"فشل حذف التعليق من يوتيوب: {e}")
            
            # Fallback to hard delete if it's the owner's own comment
            try:
                youtube = self._get_service()
                request = youtube.comments().delete(id=external_message_id)
                request.execute()
                
                msg = IncomingMessage.objects.get(external_message_id=external_message_id)
                msg.process_status = IncomingMessage.ProcessStatus.DELETED
                msg.processed_at = timezone.now()
                msg.save()
                return True
            except Exception as hard_delete_err:
                raise Exception(f"المحاولة الأولى للإخفاء: {e} | المحاولة الثانية للحذف الجذري: {hard_delete_err}")
