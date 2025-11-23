from rest_framework import serializers
from .models import Call
from users.serializers import CustomUserSerializer

class CallSerializer(serializers.ModelSerializer):
    caller = CustomUserSerializer(read_only=True)
    receiver = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Call
        fields = ['id', 'caller', 'receiver', 'status', 'started_at', 'answered_at', 'ended_at', 'duration']
        read_only_fields = ['id', 'started_at', 'duration']