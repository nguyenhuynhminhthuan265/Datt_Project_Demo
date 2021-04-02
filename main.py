from typing import List

from fastapi import Depends, FastAPI, UploadFile, File
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from config.route import Route
from connection.db_connection import get_db
from database import engine
from models.entity import models
from models.schemas import schemas
from repository import message_entity_repository
from routers import apis, api_login
from security.jwt_authorization_filter import authenticate

models.Base.metadata.create_all(bind=engine)
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

app.include_router(api_login.router, prefix=Route.V1.prefix_api, tags=['api login'])
app.include_router(apis.router, prefix=Route.V1.prefix_api, tags=['apis'], dependencies=[Depends(authenticate)])


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

    async def send_by_user_id(self, message: str, message_db: str, sender: int, receiver: int, db: Session):
        # message_entity_create = models.MessageEntity(message=message, id_user_sender=sender, id_user_receiver=receiver)
        for connection in self.active_connections:
            if connection.path_params.get('client_id') == receiver:
               # message_entity_repository.create_message_entity(db, message_entity_create)
                await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            sender = data['sender']
            receiver = data['receiver']
            message = data['message']
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
            message_entity_create = models.MessageEntity(message=message, id_user_sender=sender,
                                                         id_user_receiver=receiver)
            message_entity_repository.create_message_entity(db, message_entity_create)
            await manager.send_by_user_id(f"Client #{client_id} says: {message}", message, sender, receiver, db)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/message/", response_model=schemas.MessageEntity)
def create_message(message_entity_create: schemas.MessageEntityCreate, db: Session = Depends(get_db)):
    print(message_entity_create)
    return message_entity_repository.create_message_entity(db, message_entity_create)


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename}
