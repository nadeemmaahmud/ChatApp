from rest_framework import serializers
from .models import Message, ChatRoom
from users.serializers import CustomUserSerializer

class ChatRoomSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    participant_count = serializers.ReadOnlyField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'display_name', 'description', 'created_by', 
                 'created_at', 'is_private', 'participant_count', 'last_message']
        read_only_fields = ['id', 'created_at']

    def get_last_message(self, obj):
        last_msg = obj.last_message
        if last_msg:
            return {
                'content': last_msg.content,
                'timestamp': last_msg.timestamp,
                'user': last_msg.user.email if last_msg.user else 'Anonymous'
            }
        return None

class MessageSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    room = ChatRoomSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'user', 'room_name', 'room', 'content', 'timestamp', 'edited_at', 'is_edited']
        read_only_fields = ['id', 'timestamp', 'edited_at', 'is_edited']

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['room_name', 'content']