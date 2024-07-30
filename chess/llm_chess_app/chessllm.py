import asyncio
import time
import types
import json
from channels.generic.websocket import AsyncWebsocketConsumer

import chess
from .ai_chess_app import create_ai_chess_app
# import chess.svg
from typing_extensions import Annotated

from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_openai import OpenAI
llm = OllamaFunctions(model="llama3.1", temperature=0.1, output='json')

def  get_llm(llm_config):
    model = llm_config['model']
    api_key = llm_config['api_key']
    llm = None
    if model == 'openai-gpt-4o' or model == 'openai-gpt-4o-mini':
        llm = OpenAI(model_name=model, openai_api_key=api_key)
    elif model == 'ollama-llama3.1':
        llm = OllamaFunctions(model="llama3.1", temperature=0.1, output='json')
    return llm

# Start a websocket server to communicate with front-end.
class ChessServer(AsyncWebsocketConsumer):
    _user_input = None
    chess_iter = None
    llm = llm
    app_config = {"configurable": {"thread_id": "1"}, "recursion_limit": 500}
    def set_app_config(self, config):
        self.app_config = config

    def init_chess_iter(self, board_state, config):
        chess_app = create_ai_chess_app(self.llm, board_state, config=config)
        return chess_app.get_iterable(board_state=board_state)

    async def start_game(self, data):
        self.chess_iter = self.init_chess_iter(data.get('board_state', None), data.get('config', self.app_config))
        self.llm = get_llm(data['llm_config'])
            # llm_config = data['llm_config']
        # options = data['options']
        # chess_llm = ChessLLM(llm_config=llm_config, get_user_input=self.get_user_input, update_steps=self.update_steps, options=options)
        # chess_llm.start_game()

    async def make_move_server(self, data):
        move_dict = data['move']
        from_square = move_dict['from']
        to_square = move_dict['to']
        if from_square and to_square:
            move = chess.Move(chess.parse_square(from_square), chess.parse_square(to_square))
            move_uci = move.uci()
            result = self.chess_iter.next(move_uci) # move from user
        else:
            result = self.chess_iter.next() # move from ai
            move_uci = result['moves'][-1]
            move = chess.Move.from_uci(move_uci)

        board_state = result['board_states'][-1]
        comment = result['comments'][-1]
        return {
            'message': 'next_move_received',
            'move': {'from': chess.SQUARE_NAMES[move.from_square], 'to': chess.SQUARE_NAMES[move.to_square]},
            'comment': comment,
            'board_state': board_state
        }

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        print(text_data)
        data = json.loads(text_data)
        message = data['message']
        if message == 'start':
            await self.start_game(data)
        # elif message == 'move':
        #     self._user_input  = data['from'] + data['to']
        elif message == 'next_move':
            confirmed_move = await self.make_move_server(data)
            text_data=json.dumps(confirmed_move)
            print(text_data)
            await self.send(text_data=text_data)
        else:
            pass

        # await self.send(text_data=json.dumps({
        #     'message': message
        # }))