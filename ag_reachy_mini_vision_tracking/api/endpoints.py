import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..app_state import AppState
from .websocket.connection_manager import ConnectionManager


class AntennaState(BaseModel):
    enabled: bool


class RobotControl(BaseModel):
    direction: str


def setup_api_endpoints(
    app: FastAPI,
    shared_state: AppState,
    connection_manager: ConnectionManager,
    event_loop_ref: list,  # Mutable reference to store event loop
):
    @app.post("/antennas")
    def update_antennas_state(state: AntennaState):
        shared_state.set_antennas_enabled(state.enabled)
        return {"antennas_enabled": state.enabled}

    @app.post("/play_sound")
    def request_sound_play():
        shared_state.request_sound_play()
        return {"status": "requested"}

    @app.post("/robot_control")
    def handle_robot_control(control: RobotControl):
        valid_directions = ["up", "down", "left", "right"]
        if control.direction in valid_directions:
            shared_state.set_robot_control_command(control.direction)
            return {"status": "ok", "direction": control.direction}
        return {"status": "error", "message": "Invalid direction"}

    @app.get("/finger_count")
    def get_finger_count():
        return {"finger_count": shared_state.get_finger_count()}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        # Capture the event loop for thread-safe async operations
        if event_loop_ref[0] is None:
            event_loop_ref[0] = asyncio.get_event_loop()

        await connection_manager.connect(websocket)
        try:
            # Send initial state
            await websocket.send_json(
                {
                    "type": "finger_count",
                    "finger_count": shared_state.get_finger_count(),
                }
            )
            while True:
                data = await websocket.receive_text()
                # Echo back or handle commands if needed
                # For now, just keep the connection open
        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
        except Exception as e:
            print(f"WebSocket error: {e}")
            connection_manager.disconnect(websocket)
