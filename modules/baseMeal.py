import asyncio

from .requests import Requests


class BaseMeal:
    def __init__(self, loop: asyncio.BaseEventLoop):
        self.loop = loop
        self.requests = Requests(self.loop)
