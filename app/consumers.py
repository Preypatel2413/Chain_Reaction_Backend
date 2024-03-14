from channels.generic.websocket import AsyncWebsocketConsumer
import json

class RandomChallengeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'random_challenge'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Not needed for now
        pass

    async def game_state_update(self, event):
        message = event['message']
        player1_name = event['player1_name']
        player2_name = event['player2_name']
        room_code = event['room_code']
        await self.send(text_data=json.dumps({
            'message': message,
            'player1_name' : player1_name,
            'player2_name' : player2_name,
            'room_code' : room_code,
        }))


class GameRoom(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = 'game_%s' % self.room_code

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    

    async def receive(self, text_data):
        # data = json.loads(text_data)
        # row = data['row']
        # col = data['col']

        # # Send the received message to the room group
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': 'position_update',
        #         'row': row,
        #         'col': col
        #     }
        # )
        pass
    
    async def position_update(self, event):
        message = event['message']
        lastmove = event['lastmove']
        position = event['position']
        move = event['move']
        win = event['win']
        conv = event['conv']

        # Send the updated position to the WebSocket group
        await self.send(
            text_data=json.dumps(
            {
                'message': message,
                'lastmove': lastmove,
                'position': position,
                'move': move,
                'win': win,
                'conv': conv
            })
        )

