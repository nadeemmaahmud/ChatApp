from django.contrib import admin
from .models import Message, ChatRoom

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'created_by', 'participant_count', 'created_at')
    list_filter = ('is_private', 'created_at')
    search_fields = ('name', 'display_name')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'room_name', 'content', 'timestamp', 'is_edited')
    list_filter = ('timestamp', 'is_edited')
    search_fields = ('content', 'user__email')