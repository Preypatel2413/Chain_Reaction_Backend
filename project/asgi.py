"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path, re_path
from app.consumers import GameRoom, RandomChallengeConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# application = get_asgi_application()
ws_pattern = [
    path('ws/Game/<room_code>', GameRoom.as_asgi()),
    path('ws/random_challenge/', RandomChallengeConsumer.as_asgi()),
]

application= ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        'websocket': AuthMiddlewareStack(URLRouter(
            ws_pattern
        ))
    }
)