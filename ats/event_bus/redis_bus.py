import json
from typing import Any, Callable

import redis

from .interfaces import EventBusInterface


class RedisBus(EventBusInterface):
    def __init__(self, url: str):
        self.client = redis.Redis.from_url(url)

    def publish(self, channel: str, payload: Any) -> None:
        self.client.publish(channel, json.dumps(payload))

    def subscribe(self, channel: str, callback: Callable[[Any], None]) -> None:
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)

        for message in pubsub.listen():
            if message["type"] == "message":
                callback(json.loads(message["data"]))
