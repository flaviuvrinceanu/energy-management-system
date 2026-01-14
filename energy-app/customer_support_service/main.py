import sys
sys.path.append('/app')
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
import re
from typing import Optional, Tuple
import httpx
from shared.rabbitmq_utils import RabbitMQClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Customer Support Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


rabbitmq = None


class SupportMessage(BaseModel):
    message: str
    user_id: str


class SupportResponse(BaseModel):
    reply: str
    handled_by_rule: bool
    forwarded: bool
    source: str  # 'rule' | 'admin' | 'ai'



CHATBOT_RULES = [
    {
        "keywords": ["hello", "hi", "hey", "greetings"],
        "reply": "Hello! Welcome to Energy Management System support. How can I assist you today?",
        "pattern": r"\b(hello|hi|hey|greetings)\b"
    },
    {
        "keywords": ["help", "support", "assist"],
        "reply": "I'm here to help! You can ask me about device management, energy consumption, bills, or report issues.",
        "pattern": r"\b(help|support|assist)\b"
    },
    {
        "keywords": ["device", "add device", "create device", "new device"],
        "reply": "Only an admin can add or create new devices.Please contact your system administrator for assistance with device management.",
        "pattern": r"\b(add|create|new)\s+(device|devices)\b"
    },
    {
        "keywords": ["consumption", "energy usage", "how much energy"],
        "reply": "You can view your energy consumption in the Energy Chart section. It shows hourly energy usage for each of your devices. The system also alerts you if consumption exceeds the maximum limit.",
        "pattern": r"\b(consumption|energy\s+usage|how\s+much\s+energy)\b"
    },
    {
        "keywords": ["overconsumption", "exceeded", "alert", "warning"],
        "reply": "Overconsumption alerts are sent when a device exceeds its maximum consumption limit. Contact an admin for modifying the max consumption.",
        "pattern": r"\b(overconsumption|exceeded|alert|warning)\b"
    },
    
        
    {
        "keywords": ["password", "reset password", "forgot password", "login issue"],
        "reply": "To reset your password contact an admin. They will assist you with the password reset process.",
        "pattern": r"\b(password|reset|forgot|login\s+issue)\b"
    },
    {
        "keywords": ["delete", "remove device", "unassign"],
        "reply": "To remove a device, please contact an admin. They will assist you with the removal process. Note that this will also remove all associated energy consumption data.",
        "pattern": r"\b(delete|remove|unassign)\s+(device|devices)\b"
    },
    {
        "keywords": ["chart", "graph", "visualization", "view data"],
        "reply": "The Energy Chart displays your device consumption data in an interactive graph. You can select different devices and time periods to analyze your energy usage patterns.",
        "pattern": r"\b(chart|graph|visualization|view\s+data)\b"
    },
    {
        "keywords": ["max consumption", "limit", "threshold", "maximum"],
        "reply": "The maximum consumption is the hourly energy limit (in kWh) for each device. When a device exceeds this limit, you'll receive an overconsumption alert.",
        "pattern": r"\b(max\s+consumption|limit|threshold|maximum)\b"
    },
    {
        "keywords": ["thank", "thanks", "appreciate"],
        "reply": "You're welcome! If you have any other questions, feel free to ask. Have a great day!",
        "pattern": r"\b(thank|thanks|appreciate)\b"
    },
    {
        "keywords": ["admin", "administrator", "contact support"],
        "reply": "I'll forward your message to our admin team. They will get back to you as soon as possible.",
        "pattern": r"\b(admin|administrator|contact\s+support)\b",
        "action": "forward_to_admin",
    },
]


def match_rule(message: str) -> Tuple[bool, str, Optional[str]]:
    """Check if message matches any predefined chatbot rule"""
    message_lower = message.lower()
    
    for rule in CHATBOT_RULES:
       
        if re.search(rule["pattern"], message_lower, re.IGNORECASE):
            return True, rule["reply"], rule.get("action")
    
    return False, "", None


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


async def generate_ai_reply(message: str) -> Optional[str]:
    """Generate a reply using Google Gemini API. """

    system_prompt = (
        "You are a helpful customer support assistant for an Energy Management System. "
        "Answer concisely and practically. If the user asks about device management, explain steps in the UI. "
        "If you don't know, suggest contacting an admin."
    )

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            if not GEMINI_API_KEY:
                logger.info("Gemini AI disabled: GEMINI_API_KEY not set")
                return None

           
            model_name = GEMINI_MODEL
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"

            async def call_gemini(target_model: str):
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/"
                    f"{target_model}:generateContent?key={GEMINI_API_KEY}"
                )
                return await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [
                                    {"text": f"{system_prompt}\n\nUser: {message}"}
                                ],
                            }
                        ]
                    },
                )

            resp = await call_gemini(model_name)
            if resp.status_code == 404:
               
                fallback_model = "models/gemini-flash-latest"
                logger.warning(
                    f"Gemini model not found ({model_name}); trying {fallback_model}"
                )
                resp = await call_gemini(fallback_model)

            if resp.status_code != 200:
                logger.warning(f"Gemini request failed: {resp.status_code} {resp.text[:200]}")
                return None

            data = resp.json()
            candidates = data.get("candidates") or []
            if not candidates:
                return None
            parts = (candidates[0].get("content") or {}).get("parts") or []
            if not parts:
                return None
            text = parts[0].get("text")
            return text.strip() if text else None

    except Exception:
        logger.exception("Gemini request error")
        return None


def forward_to_admin(user_id: str, message: str):
    """Forward unhandled message to admin via RabbitMQ"""
    try:
        global rabbitmq
        if not rabbitmq:
            rabbitmq = RabbitMQClient()
            rabbitmq.connect()
            rabbitmq.declare_queue("admin_chat_queue")
        
        chat_message = {
            "type": "user_message",
            "user_id": user_id,
            "message": message,
            "timestamp": None  
        }
        
        rabbitmq.publish("admin_chat_queue", chat_message)
        logger.info(f"Forwarded message from user {user_id} to admin queue")
    
    except Exception as e:
        logger.error(f"Error forwarding to admin: {e}")


@app.post("/api/support/message", response_model=SupportResponse)
async def process_support_message(request: SupportMessage):
   
    
    try:
       
        matched, reply, action = match_rule(request.message)
        
        if matched:
            if action == "forward_to_admin":
                forward_to_admin(request.user_id, request.message)
                return SupportResponse(
                    reply=reply,
                    handled_by_rule=True,
                    forwarded=True,
                    source="admin",
                )

            return SupportResponse(
                reply=reply,
                handled_by_rule=True,
                forwarded=False,
                source="rule",
            )
        else:
            
            ai_reply = await generate_ai_reply(request.message)
            if ai_reply:
                return SupportResponse(
                    reply=ai_reply,
                    handled_by_rule=False,
                    forwarded=False,
                    source="ai",
                )

            
            forward_to_admin(request.user_id, request.message)
            return SupportResponse(
                reply="I couldn't generate an automated answer right now. I've forwarded your message to an admin.",
                handled_by_rule=False,
                forwarded=True,
                source="admin",
            )
    
    except Exception as e:
        logger.error(f"Error processing support message: {e}")
        raise HTTPException(status_code=500, detail="Error processing message")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "rules_count": len(CHATBOT_RULES)}


@app.get("/api/support/rules")
async def get_rules():
    return {
        "rules_count": len(CHATBOT_RULES),
        "rules": [
            {
                "keywords": rule["keywords"],
                "sample_reply": rule["reply"][:100] + "..."
            }
            for rule in CHATBOT_RULES
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
