from django.db import models
from django.contrib.auth import get_user_model
from users.models import CustomUser as User

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)
    participants = models.ManyToManyField(User, blank=True, related_name='chat_rooms')

    def __str__(self):
        return self.display_name or self.name

    @property
    def last_message(self):
        return self.messages.last()

    @property
    def participant_count(self):
        return self.participants.count()

class Message(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    room_name = models.CharField(max_length=255)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'[{self.timestamp}] {self.user}: {self.content}'

    def save(self, *args, **kwargs):
        # Auto-create or link to ChatRoom
        if not self.room and self.room_name:
            room, created = ChatRoom.objects.get_or_create(
                name=self.room_name,
                defaults={'display_name': self.room_name.title()}
            )
            self.room = room
        super().save(*args, **kwargs)