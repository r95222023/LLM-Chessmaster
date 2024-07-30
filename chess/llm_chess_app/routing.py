from django.urls import re_path

from . import connections, chessllm

websocket_urlpatterns = [
    re_path(r'chat/', connections.Test.as_asgi()),
    re_path(r'chess/', chessllm.ChessServer.as_asgi()),
]