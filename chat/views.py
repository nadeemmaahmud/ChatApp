from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Message, ChatRoom
from .serializers import MessageSerializer, MessageCreateSerializer, ChatRoomSerializer

class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all().order_by('-created_at')
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        room = self.get_object()
        room.participants.add(request.user)
        return Response({'detail': f'Joined room: {room.display_name}'})

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        room = self.get_object()
        room.participants.remove(request.user)
        return Response({'detail': f'Left room: {room.display_name}'})

    @action(detail=False, methods=['get'])
    def my_rooms(self, request):
        rooms = ChatRoom.objects.filter(participants=request.user).order_by('-created_at')
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Message.objects.all().order_by('-timestamp')
        room_name = self.request.query_params.get('room', None)
        if room_name:
            queryset = queryset.filter(room_name=room_name)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        from payments.models import MessageUsage
        from rest_framework.exceptions import ValidationError, PermissionDenied
        
        user = self.request.user
        message_usage, created = MessageUsage.objects.get_or_create(user=user)
        
        if not message_usage.can_send_message():
            raise PermissionDenied(detail="Message limit exceeded. Please upgrade to Pro plan.")
            
        serializer.save(user=user)
        message_usage.increment_usage()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"detail": "You can only edit your own messages."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        instance.is_edited = True
        instance.save(update_fields=['is_edited'])
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"detail": "You can only delete your own messages."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='room/(?P<room_name>[^/.]+)')
    def room_messages(self, request, room_name=None):
        messages = Message.objects.filter(room_name=room_name).order_by('timestamp')
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_messages(self, request):
        messages = Message.objects.filter(user=request.user).order_by('-timestamp')
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)