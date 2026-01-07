from loguru import logger
import os
from datetime import datetime

LOG_DIRS = [
    "logs/interactions",
    "logs/agent_decisions",
    "logs/system"
]

for log_dir in LOG_DIRS:
    os.makedirs(log_dir, exist_ok=True)

logger.add(
    "logs/system/system.log",
    level="INFO",
    rotation="5 MB",
    format="{time} | {level} | {message}"
)

logger.add(
    "logs/interactions/user_interactions.log",
    level="INFO",
    rotation="5 MB",
    format="{time} | {message}"
)

logger.add(
    "logs/agent_decisions/agent_flow.log",
    level="INFO",
    rotation="5 MB",
    format="{time} | {message}"
)

def log_user(message: str):
    logger.bind(type="user").info(message)

def log_agent(message: str):
    logger.bind(type="agent").info(message)

def log_system(message: str):
    logger.info(message)

