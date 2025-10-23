from django.db import models
from django.contrib.auth import get_user_model
from users.models import CustomUser as User

class Message(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    room_name = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'[{self.timestamp}] {self.user}: {self.content}'