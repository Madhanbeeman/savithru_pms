import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ProjectUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.project_group_name = f'project_{self.project_id}_updates'
        self.user = self.scope['user']

        await self.channel_layer.group_add(self.project_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.project_group_name, self.channel_name)

    async def send_project_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'project_update',
            'html': event.get('html'), 
            'title': event.get('title'), 
            'message': event.get('message'),
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            
            # --- NEW: Pass Photo URL ---
            'sender_profile_photo': event.get('sender_profile_photo'),
            # ---------------------------

            'timestamp': event['timestamp'],
            'image_url': event.get('image_url'),
            'file_url': event.get('file_url'),
            'file_name': event.get('file_name'),
        }))

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.room_group_name = f'user_{self.user.id}_notifications'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification', 'message': event['message'], 'link': event['link']
        }))