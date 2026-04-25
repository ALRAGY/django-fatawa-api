from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Question, IncomingMessage, ConnectedChannel
from .serializers import QuestionSerializer, IncomingMessageSerializer, ConnectedChannelSerializer
from accounts.permissions import HasAccess
from .adapters.base import PlatformRegistry

class ConnectedChannelViewSet(viewsets.ModelViewSet):
    queryset = ConnectedChannel.objects.all()
    serializer_class = ConnectedChannelSerializer
    permission_classes = [HasAccess]
    required_permission = "inbox.manage_channels"


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [HasAccess]
    required_permission = "inbox.manage_questions"


from rest_framework.decorators import action

class IncomingMessageViewSet(viewsets.ModelViewSet):
    queryset = IncomingMessage.objects.all()
    serializer_class = IncomingMessageSerializer
    permission_classes = [HasAccess]
    required_permission = "inbox.manage_messages"

    @action(detail=True, methods=['post'])
    def send_reply(self, request, pk=None):
        """
        إجراء مخصص للرد على رسالة/تعليق، ويقوم بإرسال الرد للمنصة الأصلية (مثل يوتيوب).
        متوقع في الـ body: {"reply_text": "نص الرد هنا"}
        """
        message = self.get_object()
        reply_text = request.data.get('reply_text')
        
        if not reply_text:
            return Response({"error": "يجب إرسال نص الرد 'reply_text'"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not message.channel:
            return Response({"error": "هذه الرسالة غير مرتبطة بقناة يمكن الرد عليها."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            adapter_class = PlatformRegistry.get_adapter_class(message.channel.platform_identifier)
            adapter = adapter_class(channel=message.channel)
            
            success = adapter.reply(message.external_message_id, reply_text)
            
            if success:
                # Update DB state is handled by the adapter natively, but we ensure User relation here
                message.action_taken_by = request.user
                message.save()
                return Response({"status": "تم الرد بنجاح!"})
            else:
                return Response({"error": "فشل الرد عبر المنصة لأسباب غير معروفة."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"تفاصيل الخطأ من المنصة: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def delete_external(self, request, pk=None):
        """
        إجراء لحذف التعليق تماماً من المنصة الأصلية (يوتيوب) ومن صندوق النظام.
        """
        message = self.get_object()
        if not message.channel:
            return Response({"error": "الرسالة غير مرتبطة بقناة للحذف الخارجي."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            adapter_class = PlatformRegistry.get_adapter_class(message.channel.platform_identifier)
            adapter = adapter_class(channel=message.channel)
            
            success = adapter.delete(message.external_message_id)
            if success:
                message.action_taken_by = request.user
                message.save()
                return Response({"status": "تم الحذف من المنصة بنجاح!"})
            else:
                return Response({"error": "فشل الحذف عبر المنصة لأسباب غير معروفة."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"تفاصيل الخطأ من المنصة: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class WebhookReceiverAPIView(APIView):
    """
    Endpoint for receiving webhooks dynamically based on channel ID.
    Example: /api/inbox/webhooks/1/ -> goes to the adapter of Channel 1.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, channel_id, format=None):
        payload = request.data
        try:
            channel = ConnectedChannel.objects.get(id=channel_id, is_active=True)
            adapter_class = PlatformRegistry.get_adapter_class(channel.platform_identifier)
            adapter = adapter_class(channel=channel)
            
            # Send payload into the dynamic adapter
            adapter.process_webhook(payload)
            
            return Response(
                {"status": "success", "message": "Webhook processed successfully"},
                status=status.HTTP_200_OK
            )
        except ConnectedChannel.DoesNotExist:
            return Response({"status": "error", "message": "Channel not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
             return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
