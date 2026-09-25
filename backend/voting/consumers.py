import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.room_group_name = f'trip_votes_{self.trip_id}'

        # We allow anonymous connections because we only broadcast state to the group.
        # But we could also check self.scope['user'].is_authenticated if we configure AuthMiddlewareStack.
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def vote_update(self, event):
        # Forward to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'vote_update',
            'summary': event['summary']
        }))

    async def destination_selected(self, event):
        # Forward to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'destination_selected',
            'destination_id': event['destination_id'],
            'destination_name': event['destination_name']
        }))
