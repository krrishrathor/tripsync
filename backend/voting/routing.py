from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/trips/(?P<trip_id>[0-9a-f-]+)/votes/$', consumers.VoteConsumer.as_asgi()),
]
