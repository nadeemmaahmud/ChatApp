import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Message
from users.models import CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if user is authenticated
        user = self.scope["user"]
        if isinstance(user, AnonymousUser):
            # Reject connection for unauthenticated users
            await self.close(code=4001)  # Custom close code for authentication error
            return
        
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Welcome {user.email}! You are now connected to {self.room_name}',
            'user': user.email
        }))

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            user = self.scope["user"]
            
            # Check if user is still authenticated
            if isinstance(user, AnonymousUser):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                return
            
            message = data.get('message', '').strip()
            
            if not message:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Message cannot be empty'
                }))
                return

            # Save message to database
            message_obj = await self.save_message(user, self.room_name, message)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': user.email,
                    'user_id': user.id,
                    'timestamp': message_obj.timestamp.isoformat(),
                    'message_id': message_obj.id
                }
            )
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'An error occurred while processing your message'
            }))

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    @database_sync_to_async
    def save_message(self, user, room_name, message):
        return Message.objects.create(user=user, room_name=room_name, content=message)
