import asyncio
import json
from typing import Set
from websockets.asyncio.server import serve, ServerConnection

from config.config_loader import Config
from lib.logger import Logger


class WebSocketServer:
    def __init__(self, config: Config):
        self.host = config.WEBSOCKET_HOST
        self.port = config.WEBSOCKET_PORT

        self.clients: Set[ServerConnection] = set()
        self.logger = Logger(WebSocketServer.__name__).get()
        self.server = None
        self.loop = None

    async def register(self, websocket: ServerConnection):
        self.clients.add(websocket)
        self.logger.info(f"Client connected. Total clients: {len(self.clients)}")

    async def unregister(self, websocket: ServerConnection):
        self.clients.discard(websocket)
        self.logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def handler(self, websocket: ServerConnection):
        await self.register(websocket)
        try:
            async for message in websocket:
                self.logger.debug(f"Received message: {message}")
        except Exception as e:
            self.logger.debug(f"Connection error: {e}")
        finally:
            await self.unregister(websocket)

    async def broadcast(self, message: dict):
        if self.clients:
            message_json = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_json) for client in self.clients],
                return_exceptions=True,
            )

    async def start_server(self):
        self.server = await serve(self.handler, self.host, self.port)
        self.logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop_server(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")

    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start_server())
        self.loop.run_forever()

    def stop(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
