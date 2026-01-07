from fastapi import APIRouter
from pydantic import BaseModel
from src.agents.receptionist_agent import ReceptionistAgent
from src.utils.logger import log_user

router = APIRouter()
receptionist = ReceptionistAgent()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(req: ChatRequest):
    log_user(f"User message: {req.message}")

    if receptionist.patient_data is None:
        return {"response": receptionist.handle_name(req.message)}

    route = receptionist.route_query(req.message)

    if route == "medical":
        return {
            "response": "This looks like a medical concern. Let me connect you to our Clinical AI Agent."
        }

    return {"response": "Thank you for the update. Please continue monitoring your health."}
