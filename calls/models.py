from django.db import models
from django.conf import settings
import uuid

class Call(models.Model):
    CALL_STATUS = (
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('rejected', 'Rejected'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='incoming_calls')
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='initiated')
    started_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"Call from {self.caller} to {self.receiver} - {self.status}"