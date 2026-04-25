from rest_framework import serializers
from .models import Question, IncomingMessage, ConnectedChannel
from django.contrib.auth import get_user_model

User = get_user_model()

class ConnectedChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectedChannel
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'username', 'email') # Update based on your actual user fields if needed


class IncomingMessageSerializer(serializers.ModelSerializer):
    action_taken_by_details = UserBasicSerializer(source='action_taken_by', read_only=True)
    target_question_details = QuestionSerializer(source='target_question', read_only=True)
    channel_details = ConnectedChannelSerializer(source='channel', read_only=True)
    
    class Meta:
        model = IncomingMessage
        fields = '__all__'
        read_only_fields = ('id', 'received_at')

class WebhookPayloadSerializer(serializers.Serializer):
    """
    Serializer to document the expected incoming raw payload if we wanted to
    validate structure before passing to normalizer. Let's keep it simple for now
    as normalizers handle specific parsing.
    """
    pass
