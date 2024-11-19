from typing import Dict, List
import aiohttp
import asyncio
import logging
import json
from app.services.redis_service import redis_service  # Import Redis service for history management

logger = logging.getLogger(__name__)

async def send_to_ollama_service(conversation_id: str, user_message: str, prompt: str = "") -> Dict:
    """
    Sends the user_message to the Ollama service with chat history from Redis.
    Includes an optional prompt as a system-level message.
    """
    print("send_to_ollama_service")
    ollama_api_url = "http://ollama:11434/api/chat"  # Updated to the chat endpoint
    headers = {
        "Content-Type": "application/json",
        # "Authorization": "Bearer YOUR_API_TOKEN"  # Replace with actual token if required
    }

    # Fetch chat history from Redis
    existing_history = await redis_service.get(conversation_id)
    if not existing_history:
        existing_history = []

    # Add the new user message to the chat history
    new_message = {"role": "user", "content": user_message}
    if prompt:
        # Add the system prompt if available
        existing_history.append({"role": "system", "content": prompt})
    existing_history.append(new_message)

    payload = {
        "model": "llama3.1:8b",
        "messages": existing_history,
        "stream": False,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(ollama_api_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Received response from Ollama service.")

                    # Add Ollama's response to chat history
                    assistant_message = data.get("message", {}).get("content", "")
                    if assistant_message:
                        existing_history.append({"role": "assistant", "content": assistant_message})

                        # Save updated history back to Redis
                        await redis_service.set(conversation_id, existing_history)

                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama service returned status {response.status}: {error_text}")
                    return {}
    except Exception as e:
        logger.error(f"Failed to communicate with Ollama service: {e}")
        return {}
