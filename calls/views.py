from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Call
from .serializers import CallSerializer

class CallHistoryView(generics.ListAPIView):
    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Call.objects.filter(
            caller=self.request.user
        ) | Call.objects.filter(
            receiver=self.request.user
        )

class CallDetailView(generics.RetrieveAPIView):
    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated]
    queryset = Call.objects.all()
