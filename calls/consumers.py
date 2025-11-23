import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Call
from users.models import CustomUser as User

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_group_name = None
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        self.user_id = str(self.user.id)
        self.room_group_name = f'user_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
    async def receive(self, text_data):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }))
            return
        
        message_type = data.get('type')
        
        if message_type == 'call_initiate':
            await self.initiate_call(data)
        elif message_type == 'call_answer':
            await self.answer_call(data)
        elif message_type == 'call_reject':
            await self.reject_call(data)
        elif message_type == 'call_end':
            await self.end_call(data)
        elif message_type == 'ice_candidate':
            await self.forward_ice_candidate(data)
        elif message_type == 'offer':
            await self.forward_offer(data)
        elif message_type == 'answer':
            await self.forward_answer(data)
            
    async def initiate_call(self, data):
        receiver_id = data.get('receiver_id')
        receiver = await self.get_user(receiver_id)
        
        if not receiver:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'User not found'
            }))
            return
            
        call = await self.create_call(self.user, receiver)
        
        await self.channel_layer.group_send(
            f'user_{receiver_id}',
            {
                'type': 'incoming_call',
                'call_id': str(call.id),
                'caller': {
                    'id': str(self.user.id),
                    'email': self.user.email,
                    'first_name': self.user.first_name,
                    'last_name': self.user.last_name,
                }
            }
        )
        
        await self.send(text_data=json.dumps({
            'type': 'call_initiated',
            'call_id': str(call.id),
            'receiver': {
                'id': str(receiver.id),
                'email': receiver.email,
                'first_name': receiver.first_name,
                'last_name': receiver.last_name,
            }
        }))
        
    async def answer_call(self, data):
        call_id = data.get('call_id')
        call = await self.update_call_status(call_id, 'answered')
        
        if call:
            caller_id = await self.get_caller_id(call_id)
            await self.channel_layer.group_send(
                f'user_{caller_id}',
                {
                    'type': 'call_answered',
                    'call_id': str(call.id)
                }
            )
            
    async def reject_call(self, data):
        call_id = data.get('call_id')
        call = await self.update_call_status(call_id, 'rejected')
        
        if call:
            caller_id = await self.get_caller_id(call_id)
            await self.channel_layer.group_send(
                f'user_{caller_id}',
                {
                    'type': 'call_rejected',
                    'call_id': str(call.id)
                }
            )
            
    async def end_call(self, data):
        call_id = data.get('call_id')
        call_info = await self.end_call_record(call_id)
        
        if call_info:
            caller_id, receiver_id = call_info
            other_user_id = str(receiver_id if str(caller_id) == self.user_id else caller_id)
            
            await self.channel_layer.group_send(
                f'user_{other_user_id}',
                {
                    'type': 'call_ended',
                    'call_id': str(call_id)
                }
            )
            
    async def forward_ice_candidate(self, data):
        target_id = data.get('target_id')
        candidate = data.get('candidate')
        
        await self.channel_layer.group_send(
            f'user_{target_id}',
            {
                'type': 'ice_candidate',
                'candidate': candidate,
                'from_user': self.user_id
            }
        )
        
    async def forward_offer(self, data):
        target_id = data.get('target_id')
        offer = data.get('offer')
        call_id = data.get('call_id')
        
        await self.channel_layer.group_send(
            f'user_{target_id}',
            {
                'type': 'offer',
                'offer': offer,
                'call_id': call_id,
                'from_user': self.user_id
            }
        )
        
    async def forward_answer(self, data):
        target_id = data.get('target_id')
        answer = data.get('answer')
        call_id = data.get('call_id')
        
        await self.channel_layer.group_send(
            f'user_{target_id}',
            {
                'type': 'answer',
                'answer': answer,
                'call_id': call_id,
                'from_user': self.user_id
            }
        )
        
    async def incoming_call(self, event):
        await self.send(text_data=json.dumps(event))
        
    async def call_answered(self, event):
        await self.send(text_data=json.dumps(event))
        
    async def call_rejected(self, event):
        await self.send(text_data=json.dumps(event))
        
    async def call_ended(self, event):
        await self.send(text_data=json.dumps(event))
        
    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps(event))
        
    async def offer(self, event):
        await self.send(text_data=json.dumps(event))
        
    async def answer(self, event):
        await self.send(text_data=json.dumps(event))
        
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
            
    @database_sync_to_async
    def create_call(self, caller, receiver):
        return Call.objects.create(caller=caller, receiver=receiver, status='initiated')
        
    @database_sync_to_async
    def update_call_status(self, call_id, status):
        try:
            call = Call.objects.get(id=call_id)
            call.status = status
            if status == 'answered':
                call.answered_at = timezone.now()
            call.save()
            return call
        except Call.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_caller_id(self, call_id):
        try:
            call = Call.objects.get(id=call_id)
            return str(call.caller.id)
        except Call.DoesNotExist:
            return None
            
    @database_sync_to_async
    def end_call_record(self, call_id):
        try:
            call = Call.objects.get(id=call_id)
            call.status = 'ended'
            call.ended_at = timezone.now()
            if call.answered_at:
                call.duration = int((call.ended_at - call.answered_at).total_seconds())
            call.save()
            return (call.caller.id, call.receiver.id)
        except Call.DoesNotExist:
            return None