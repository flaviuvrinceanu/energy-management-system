import sys
sys.path.append('/app')
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import jwt
import os
import logging
import asyncio
from typing import Dict, Set
import json
from shared.rabbitmq_utils import RabbitMQClient
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "secret-key")

SUPPORT_SERVICE_URL = os.getenv("SUPPORT_SERVICE_URL", "http://support:8005").rstrip("/")

app = FastAPI(title="WebSocket Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


notification_connections: Dict[str, Set[WebSocket]] = {}
chat_connections: Dict[str, Set[WebSocket]] = {}
admin_chat_connections: Set[WebSocket] = set()


connections_lock = asyncio.Lock()


def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def broadcast_to_user(user_id: str, message: dict, connection_pool: Dict[str, Set[WebSocket]]):
    """Broadcast message to all websocket connections of a specific user"""
    async with connections_lock:
        if user_id in connection_pool:
            disconnected = set()
            for websocket in connection_pool[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.add(websocket)
            
           
            connection_pool[user_id] -= disconnected
            if not connection_pool[user_id]:
                del connection_pool[user_id]


async def broadcast_to_admins(message: dict):
    """Broadcast message to all admin websocket connections"""
    global admin_chat_connections
    async with connections_lock:
        disconnected = set()
        for websocket in admin_chat_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to admin: {e}")
                disconnected.add(websocket)
        
        
        admin_chat_connections.difference_update(disconnected)


@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time overconsumption notifications"""
    try:
        
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        await websocket.accept()
        logger.info(f"User {user_id} connected to notifications")
        
        
        async with connections_lock:
            if user_id not in notification_connections:
                notification_connections[user_id] = set()
            notification_connections[user_id].add(websocket)
        
        try:
            
            while True:
                data = await websocket.receive_text()
               
                if data == "ping":
                    await websocket.send_text("pong")
        
        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected from notifications")
        
        finally:
            
            async with connections_lock:
                if user_id in notification_connections:
                    notification_connections[user_id].discard(websocket)
                    if not notification_connections[user_id]:
                        del notification_connections[user_id]
    
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
    except Exception as e:
        logger.error(f"Error in notifications websocket: {e}")
        await websocket.close(code=1011, reason="Internal error")


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for customer support chat"""
    global admin_chat_connections
    try:
        
        payload = decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role", "client")
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        await websocket.accept()
        logger.info(f"User {user_id} (role={role}) connected to chat")
        
        
        async with connections_lock:
            if role == "admin":
                admin_chat_connections.add(websocket)
            else:
                if user_id not in chat_connections:
                    chat_connections[user_id] = set()
                chat_connections[user_id].add(websocket)
        
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                
               
                if role == "admin":
                    
                    target_user_id = message_data.get("target_user_id")
                    if target_user_id:
                        reply_message = {
                            "type": "admin_reply",
                            "message": message_data.get("message"),
                            "timestamp": message_data.get("timestamp")
                        }
                        await broadcast_to_user(target_user_id, reply_message, chat_connections)
                        logger.info(f"Admin replied to user {target_user_id}")
                
                else:
                    
                    import httpx
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                f"{SUPPORT_SERVICE_URL}/api/support/message",
                                json={
                                    "message": message_data.get("message"),
                                    "user_id": user_id
                                },
                                timeout=5.0
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                               
                                reply = {
                                    "type": "bot_reply",
                                    "message": result.get("reply"),
                                    "handled_by_rule": result.get("handled_by_rule"),
                                    "forwarded": result.get("forwarded"),
                                    "timestamp": message_data.get("timestamp")
                                }
                                await websocket.send_json(reply)
                                
                               
                                if result.get("forwarded"):
                                    admin_notification = {
                                        "type": "new_user_message",
                                        "user_id": user_id,
                                        "message": message_data.get("message"),
                                        "timestamp": message_data.get("timestamp")
                                    }
                                    await broadcast_to_admins(admin_notification)
                    
                    except Exception as e:
                        logger.exception("Error calling support service")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Support service unavailable"
                        })
        
        except WebSocketDisconnect:
            logger.info(f"User {user_id} (role={role}) disconnected from chat")
        
        finally:
            
            async with connections_lock:
                if role == "admin":
                    admin_chat_connections.discard(websocket)
                else:
                    if user_id in chat_connections:
                        chat_connections[user_id].discard(websocket)
                        if not chat_connections[user_id]:
                            del chat_connections[user_id]
    
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
    except Exception as e:
        logger.error(f"Error in chat websocket: {e}")
        await websocket.close(code=1011, reason="Internal error")



def consume_overconsumption_notifications():
    """Background thread to consume overconsumption notifications from RabbitMQ"""
    rabbitmq = RabbitMQClient()
    
    def handle_notification(message: dict):
        """Handle overconsumption notification"""
        try:
            user_id = message.get("user_id")
            if user_id:
                
                asyncio.run_coroutine_threadsafe(
                    broadcast_to_user(user_id, message, notification_connections),
                    app.state.loop
                )
                logger.info(f"Broadcasted overconsumption notification to user {user_id}")
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    try:
        rabbitmq.connect()
        rabbitmq.declare_exchange("overconsumption_notifications", "fanout")
        rabbitmq.declare_queue("websocket_notifications_queue")
        rabbitmq.bind_queue_to_exchange("websocket_notifications_queue", "overconsumption_notifications")
        logger.info("Started consuming overconsumption notifications")
        rabbitmq.consume("websocket_notifications_queue", handle_notification)
    except Exception as e:
        logger.error(f"Error in RabbitMQ consumer: {e}")


@app.on_event("startup")
async def startup_event():
    """Start background RabbitMQ consumer on startup"""
    app.state.loop = asyncio.get_event_loop()
    
   
    consumer_thread = threading.Thread(
        target=consume_overconsumption_notifications,
        daemon=True
    )
    consumer_thread.start()
    logger.info("WebSocket service started")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "notification_users": len(notification_connections),
        "chat_users": len(chat_connections),
        "admin_connections": len(admin_chat_connections)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
