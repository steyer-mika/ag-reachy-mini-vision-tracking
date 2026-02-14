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

        # Track connected clients for broadcasting
        self.clients: Set[ServerConnection] = set()
        self.logger = Logger(WebSocketServer.__name__).get()
        self.server = None

        # Event loop reference - needed for cross-thread communication
        # This is set when start() is called in the server thread
        self.loop = None

    async def register(self, websocket: ServerConnection) -> None:
        self.clients.add(websocket)
        self.logger.info(f"Client connected. Total clients: {len(self.clients)}")

    async def unregister(self, websocket: ServerConnection) -> None:
        self.clients.discard(websocket)
        self.logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def handler(self, websocket: ServerConnection) -> None:
        await self.register(websocket)
        try:
            # Listen for incoming messages (connection stays open)
            # We don't expect client messages, but this keeps the connection alive
            async for message in websocket:
                self.logger.debug(f"Received message: {message}")
        except Exception as e:
            self.logger.debug(f"Connection error: {e}")
        finally:
            await self.unregister(websocket)

    async def broadcast(self, message: dict) -> None:
        if self.clients:
            message_json = json.dumps(message)
            # Send to all clients concurrently, don't fail if some clients error
            await asyncio.gather(
                *[client.send(message_json) for client in self.clients],
                return_exceptions=True,
            )

    async def start_server(self) -> None:
        self.server = await serve(self.handler, self.host, self.port)
        self.logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop_server(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()

            # Cancel all pending tasks except the current one
            tasks = [t for t in asyncio.all_tasks(self.loop) if not t.done()]
            for task in tasks:
                task.cancel()

            # Wait for all tasks to complete cancellation
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self.logger.info("WebSocket server stopped")

    def start(self) -> None:
        # Create a new event loop for this thread
        # (asyncio event loops are not thread-safe and each thread needs its own)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Start server and run until stopped
            self.loop.run_until_complete(self.start_server())
            self.loop.run_forever()
        finally:
            # Clean up any remaining tasks
            try:
                # Cancel all remaining tasks
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()

                # Wait for task cancellation to complete
                if pending:
                    self.loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception as e:
                self.logger.debug(f"Error during loop cleanup: {e}")
            finally:
                self.loop.close()

    def stop(self) -> None:
        if self.loop and self.loop.is_running():
            # Schedule the stop_server coroutine and then stop the loop
            asyncio.run_coroutine_threadsafe(self.stop_server(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)
