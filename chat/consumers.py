import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Message
from subscriptions.models import MessageUsage, Subscription

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        user = self.scope.get("user", AnonymousUser())
        
        print(f"🔗 WebSocket connection attempt for room: {self.room_name}")
        print(f"👤 User: {user.email if hasattr(user, 'email') else 'Anonymous'}")
        
        if isinstance(user, AnonymousUser):
            print("⚠️ Anonymous user connecting - allowing for development")
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        print(f"✅ Connection accepted for room: {self.room_name}")
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Welcome! You are now connected to room: {self.room_name}',
            'user': user.email if hasattr(user, 'email') else 'Anonymous',
            'room': self.room_name
        }))
        
        if not isinstance(user, AnonymousUser):
            await self.send_message_history()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            if not text_data or text_data.strip() == "":
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Empty message received'
                }))
                return
            
            if isinstance(text_data, bytes):
                text_data = text_data.decode('utf-8')
            
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                if text_data.strip().startswith('{') and text_data.strip().endswith('}'):
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Malformed JSON'
                    }))
                    return
                else:
                    data = {'message': text_data.strip()}
            
            user = self.scope.get("user", AnonymousUser())
            
            print(f"📨 Received message from user: {user.email if hasattr(user, 'email') else 'Anonymous'}")
            
            if not isinstance(user, AnonymousUser):
                can_send = await self.check_message_limit(user)
                if not can_send:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Message limit reached. Please upgrade to Pro plan for unlimited messages.',
                        'error_code': 'MESSAGE_LIMIT_EXCEEDED'
                    }))
                    return
            
            user_display = user.email if hasattr(user, 'email') else 'Anonymous'
            
            message = ""
            if isinstance(data, dict):
                message = data.get('message', '').strip()
            elif isinstance(data, str):
                message = data.strip()
            else:
                message = str(data).strip()
            
            if not message:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Message content cannot be empty'
                }))
                return

            message_obj = None
            if not isinstance(user, AnonymousUser):
                message_obj = await self.save_message(user, self.room_name, message)
                await self.increment_message_usage(user)
                print(f"💾 Message saved with ID: {message_obj.id}")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': user_display,
                    'user_id': user.id if hasattr(user, 'id') else None,
                    'timestamp': message_obj.timestamp.isoformat() if message_obj else None,
                    'message_id': message_obj.id if message_obj else None
                }
            )
            
        except Exception as e:
            print(f"❌ Error in receive method: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Server error occurred'
            }))

    async def chat_message(self, event):
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

    @database_sync_to_async
    def get_recent_messages(self, room_name, limit=20):
        messages = Message.objects.filter(
            room_name=room_name
        ).select_related('user').order_by('-timestamp')[:limit]
        return list(reversed(messages))

    async def send_message_history(self):
        try:
            recent_messages = await self.get_recent_messages(self.room_name)
            
            if recent_messages:
                await self.send(text_data=json.dumps({
                    'type': 'message_history',
                    'messages': [
                        {
                            'id': msg.id,
                            'message': msg.content,
                            'username': msg.user.email,
                            'user_id': msg.user.id,
                            'timestamp': msg.timestamp.isoformat()
                        } for msg in recent_messages
                    ]
                }))
        except Exception:
            pass

    @database_sync_to_async
    def check_message_limit(self, user):
        try:
            usage, created = MessageUsage.objects.get_or_create(user=user)
            return usage.can_send_message()
        except Exception as e:
            print(f"Error checking message limit: {e}")
            return True

    @database_sync_to_async
    def increment_message_usage(self, user):
        try:
            usage, created = MessageUsage.objects.get_or_create(user=user)
            usage.increment_message_count()
        except Exception as e:
            print(f"Error incrementing message usage: {e}")

    @database_sync_to_async
    def get_user_message_status(self, user):
        try:
            usage, created = MessageUsage.objects.get_or_create(user=user)
            usage.reset_daily_count()
            
            status = {
                'messages_sent_today': usage.messages_sent_today,
                'can_send_message': usage.can_send_message(),
                'subscription_type': 'basic'
            }
            
            try:
                subscription = user.subscription
                if subscription.is_active and not subscription.is_expired:
                    status['subscription_type'] = 'pro'
                    status['subscription_plan'] = subscription.plan.name
                    status['days_remaining'] = subscription.days_remaining
                    if subscription.plan.message_limit == -1:
                        status['remaining_messages'] = 'unlimited'
                    else:
                        status['remaining_messages'] = max(0, subscription.plan.message_limit - usage.messages_sent_today)
                else:
                    status['remaining_messages'] = max(0, 50 - usage.messages_sent_today)
            except Subscription.DoesNotExist:
                status['remaining_messages'] = max(0, 50 - usage.messages_sent_today)
            
            return status
        except Exception as e:
            print(f"Error getting user message status: {e}")
            return {'can_send_message': True, 'subscription_type': 'basic'}
