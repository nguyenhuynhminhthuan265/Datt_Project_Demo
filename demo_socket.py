import json
from collections import defaultdict
from typing import List, Optional

from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, Request, Response, Cookie, Query, Depends
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette import status
from starlette.background import BackgroundTasks
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:5000",
    "https://localhost:5000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#
# # locate templates
# templates = Jinja2Templates(directory="templates")
#
#
# @app.get("/")
# def get_home(request: Request):
#     return templates.TemplateResponse("home.html", {"request": request})
#
#
# @app.get("/chat")
# def get_chat(request: Request):
#     return templates.TemplateResponse("chat.html", {"request": request})
#
#
# @app.get("/api/current_user")
# def get_user(request: Request):
#     return request.cookies.get("X-Authorization")
#
#
# class RegisterValidator(BaseModel):
#     username: str
#
#
# @app.post("/api/register")
# def register_user(user: RegisterValidator, response: Response):
#     response.set_cookie(key="X-Authorization", value=user.username, httponly=True)
#
#
# class SocketManager:
#     def __init__(self):
#         self.active_connections: List[(WebSocket, str)] = []
#
#     async def connect(self, websocket: WebSocket, user: str):
#         await websocket.accept()
#         self.active_connections.append((websocket, user))
#
#     def disconnect(self, websocket: WebSocket, user: str):
#         self.active_connections.remove((websocket, user))
#
#     async def broadcast(self, data: dict):
#         for connection in self.active_connections:
#             await connection[0].send_json(data)
#
#
# manager = SocketManager()
#
#
# @app.websocket("/api/chat")
# async def chat(websocket: WebSocket):
#     sender = websocket.cookies.get("X-Authorization")
#     if sender:
#         await manager.connect(websocket, sender)
#         response = {
#             "sender": sender,
#             "message": "got connected"
#         }
#         await manager.broadcast(response)
#         try:
#             while True:
#                 data = await websocket.receive_json()
#                 await manager.broadcast(data)
#         except WebSocketDisconnect:
#             manager.disconnect(websocket, sender)
#             response['message'] = "left"
#             await manager.broadcast(response)

# =====================================


from typing import List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            print(connection.path_params.get('client_id'))
            await connection.send_text(message)

    async def send_by_user_id(self, message: str, sender: int, receiver: int, websocket: WebSocket):
        for connection in self.active_connections:
            if connection.path_params.get('client_id') == receiver:
                await connection.send_text(message)


manager = ConnectionManager()


class Notifier:
    """
        Manages chat room sessions and members along with message routing
    """

    def __init__(self):
        self.connections: dict = defaultdict(dict)
        self.generator = self.get_notification_generator()

    async def get_notification_generator(self):
        while True:
            message = yield
            msg = message["message"]
            room_name = message["room_name"]
            await self._notify(msg, room_name)

    def get_members(self, room_name):
        try:
            return self.connections[room_name]
        except Exception:
            return None

    async def push(self, msg: str, room_name: str = None):
        message_body = {"message": msg, "room_name": room_name}
        await self.generator.asend(message_body)

    async def connect(self, websocket: WebSocket, room_name: str):
        await websocket.accept()
        if self.connections[room_name] == {} or len(self.connections[room_name]) == 0:
            self.connections[room_name] = []
        self.connections[room_name].append(websocket)
        print(f"CONNECTIONS : {self.connections[room_name]}")

    def remove(self, websocket: WebSocket, room_name: str):
        self.connections[room_name].remove(websocket)
        print(
            f"CONNECTION REMOVED\nREMAINING CONNECTIONS : {self.connections[room_name]}"
        )

    async def _notify(self, message: str, room_name: str):
        living_connections = []
        while len(self.connections[room_name]) > 0:
            websocket = self.connections[room_name].pop()
            await websocket.send_text(message)
            living_connections.append(websocket)
        self.connections[room_name] = living_connections


notifier = Notifier()


async def get_cookie_or_token(
        websocket: WebSocket,
        session: Optional[str] = Cookie(None),
        token: Optional[str] = Query(None),
):
    if session is None and token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@app.websocket("/items/{item_id}/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        item_id: str,
        q: Optional[int] = None,
        cookie_or_token: str = Depends(get_cookie_or_token),
):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(
            f"Session cookie or query token value is: {cookie_or_token}"
        )
        if q is not None:
            await websocket.send_text(f"Query parameter q is: {q}")
        await websocket.send_text(f"Message text was: {data}, for item ID: {item_id}")


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            sender = data['sender']
            receiver = data['receiver']
            message = data['message']
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
            await manager.send_by_user_id(f"Client #{client_id} says: {message}", sender, receiver, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/{room_name}")
async def websocket_endpoint(
        websocket: WebSocket, room_name: str, background_tasks: BackgroundTasks
):
    print(room_name)
    await notifier.connect(websocket, room_name)

    try:
        while True:
            data = await websocket.receive_text()
            d = json.loads(data)
            d["room_name"] = room_name

            room_members = (
                notifier.get_members(room_name)
                if notifier.get_members(room_name) is not None
                else []
            )
            if websocket not in room_members:
                print("SENDER NOT IN ROOM MEMBERS: RECONNECTING")
                await notifier.connect(websocket, room_name)

            await notifier._notify(f"{data}", room_name)
    except WebSocketDisconnect:
        notifier.remove(websocket, room_name)

# ====================================================

# locate templates
# templates = Jinja2Templates(directory="templates")
#
#
# @app.get("/")
# def get_home(request: Request):
#     return templates.TemplateResponse("home.html", {"request": request})
#
#
# @app.get("/chat")
# def get_chat(request: Request):
#     return templates.TemplateResponse("chat.html", {"request": request})
#
#
# @app.get("/api/current_user")
# def get_user(request: Request):
#     return request.cookies.get("X-Authorization")
#
#
# class RegisterValidator(BaseModel):
#     username: str
#
#
# @app.post("/api/register")
# def register_user(user: RegisterValidator, response: Response):
#     response.set_cookie(key="X-Authorization", value=user.username, httponly=True)
#
#
# class SocketManager:
#     def __init__(self):
#         self.active_connections: List[(WebSocket, str)] = []
#
#     async def connect(self, websocket: WebSocket, user: str):
#         await websocket.accept()
#         self.active_connections.append((websocket, user))
#
#     def disconnect(self, websocket: WebSocket, user: str):
#         self.active_connections.remove((websocket, user))
#
#     async def broadcast(self, data: dict):
#         for connection in self.active_connections:
#             await connection[0].send_json(data)
#
#
# manager = SocketManager()
#
#
# @app.websocket("/api/chat")
# async def chat(websocket: WebSocket):
#     sender = websocket.cookies.get("X-Authorization")
#     if sender:
#         await manager.connect(websocket, sender)
#         response = {
#             "sender": sender,
#             "message": "got connected"
#         }
#         await manager.broadcast(response)
#         try:
#             while True:
#                 data = await websocket.receive_json()
#                 await manager.broadcast(data)
#         except WebSocketDisconnect:
#             manager.disconnect(websocket, sender)
#             response['message'] = "left"
#             await manager.broadcast(response)
