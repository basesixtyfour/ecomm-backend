from rest_framework import serializers

from .models import ChatRoom


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ["id", "status", "created_at"]
        read_only_fields = fields


class AgentChatRoomSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ChatRoom
        fields = ["id", "username", "status", "created_at"]
        read_only_fields = fields
