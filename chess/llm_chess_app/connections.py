import json
from channels.generic.websocket import AsyncWebsocketConsumer
# import base64
# inspired by https://medium.com/django-unleashed/websockets-based-apis-with-django-real-time-communication-made-easy-2122b49720bf
class Test(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    async def disconnect(self, close_code):
        pass

    # handle binary data here
    # async def receive(self, text_data):
    #     bytes_data = base64.b64decode(text_data)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        print(message)
        await self.send(text_data=json.dumps(text_data_json))

# Background Tasks

# from asgiref.sync import async_to_sync
# from channels.generic.sync import SyncConsumer

# class TaskConsumer(SyncConsumer):
#     def task(self, message):
#         # long-running or asynchronous task
#         return 'Task complete!'
# async def receive(self, text_data):
#     message = json.loads(text_data)
#     task_type = message['task_type']
#     task_args = message['task_args']
#     response = await async_to_sync(TaskConsumer().task)(task_args)
#     await self.send(text_data=json.dumps({
#         'response': response
#     }))

# Group communication

# from channels.layers import get_channel_layer
# channel_layer = get_channel_layer()

# async def connect(self):
#     self.room_name = self.scope['url_route']['kwargs']['room_name']
#     self.room_group_name = 'chat_%s' % self.room_name

#     await self.channel_layer.group_add(
#         self.room_group_name,
#         self.channel_name
#     )

#     await self.accept()

# async def disconnect(self, close_code):
#     await self.channel_layer.group_discard(
#         self.room_group_name,
#         self.channel_name
#     )

# async def receive(self, text_data):
#     text_data_json = json.loads(text_data)
#     message = text_data_json['message']

#     await self.channel_layer.group_send(
#         self.room_group_name,
#         {
#             'type': 'chat_message',
#             'message': message
#         }
#     )

# async def chat_message(self, event):
#     message = event['message']

#     await self.send(text_data=json.dumps({
#         'message': message
#     }))