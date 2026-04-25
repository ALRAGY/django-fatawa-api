from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionViewSet, IncomingMessageViewSet, WebhookReceiverAPIView, ConnectedChannelViewSet

router = DefaultRouter()
router.register(r'channels', ConnectedChannelViewSet, basename='channel')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'messages', IncomingMessageViewSet, basename='incoming-message')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/<int:channel_id>/', WebhookReceiverAPIView.as_view(), name='webhook-receiver'),
]
