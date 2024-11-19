import asyncio
import re
from typing import List, Dict, Tuple
from fastapi import HTTPException
from app.services.file_processing import process_files
from app.services.ollama_service import send_to_ollama_service
from app.sockets.base import sio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Define Namespace
chat_namespace = "/chat-socket"

# Allowed file types
ALLOWED_FILE_TYPES = {
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}


def extract_prompts_from_text(text: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Extract prompts from the text body.
    Prompts are expected in the format: **Attached Prompts:** <Title>: <Description>
    """
    prompt_pattern = r"\*\*Attached Prompts:\*\*(.*)"
    match = re.search(prompt_pattern, text, re.DOTALL)

    prompts = []
    if match:
        prompts_text = match.group(1).strip()
        for line in prompts_text.split("\n"):
            line = line.strip()
            if ":" in line:
                title, description = line.split(":", 1)
                prompts.append({"title": title.strip(), "description": description.strip()})

        text = text[:match.start()].strip()

    return text, prompts


@sio.on("sendMessage", namespace=chat_namespace)
async def handle_send_message(sid: str, data: Dict):
    """
    Handle incoming messages or file uploads from clients.
    """
    try:
        # Extract inputs
        user_message = data.get("message", {}).get("text", "").strip()
        files = data.get("message", {}).get("attachments", [])
        prompt = data.get("prompt", "")
        conversation_id = data.get("conversationId")
        if not conversation_id:
            raise ValueError("Missing conversationId.")
        # Check for empty message or files
        if not user_message and not files:
            raise ValueError("No message or files provided.")

        # Directly extract text and prepare file results
        extracted_text, file_results = await process_preprocessed_files(files)
        user_message = f"{user_message} {extracted_text}".strip()

        # Default message if only files were uploaded
        if not user_message:
            user_message = "Uploaded files only."

        # Emit processing status
        await sio.emit(
            "processingStart",
            {"status": "Analyzing input..."},
            room=sid,
            namespace=chat_namespace,
        )

        # Limit user message length to 2000 characters
        if len(user_message) > 2000:
            user_message = user_message[:2000]

        # Pass the conversationId, message, and prompt to Ollama service
        ai_response = await send_to_ollama_service(conversation_id, user_message, prompt)

        if not ai_response or "message" not in ai_response:
            raise ValueError("Invalid response from Ollama service.")

        # Prepare chat entry for client response
        chat_entry = {
            "conversationId": conversation_id,
            "message": {
                "type": "received",
                "text": ai_response["message"].get("content", ""),
                "time": datetime.now().isoformat() + "Z",
                "attachments": file_results if file_results else [],
            },
        }

        # Emit the new message to the client
        await sio.emit("newMessage", chat_entry, room=sid, namespace=chat_namespace)

    except ValueError as ve:
        await emit_error(sid, str(ve))
    except Exception as e:
        logger.error(f"Unexpected Error for sid={sid}: {e}")
        await emit_error(sid, "An unexpected error occurred. Please try again later.")


async def process_preprocessed_files(files: List[Dict]) -> Tuple[str, List[Dict]]:
    """
    Handle already preprocessed files.
    Extract text and prepare attachments from given file data.
    """
    if not files:
        logger.info("No files to process.")
        return "", []

    extracted_text = []
    attachments = []

    for file in files:
        try:
            # Extract necessary details
            file_text = file.get("extracted_text", "").strip()
            file_name = file.get("file_name", "Uploaded File")
            file_summary = file.get("summary", "")
            file_tags = file.get("tags", [])

            extracted_text.append(file_text)

            # Prepare attachment
            attachment = {
                "type": "file",
                "text": file_name,
                "summary": file_summary,
                "tags": file_tags,
                "file_id": file.get("file_id"),
            }
            attachments.append(attachment)
        except Exception as e:
            logger.error(f"Error processing preprocessed file: {e}")
            continue

    return " ".join(extracted_text).strip(), attachments


async def emit_error(sid: str, error_message: str):
    """
    Emit error messages to the client asynchronously.
    """
    await sio.emit(
        "error",
        {"error": error_message},
        room=sid,
        namespace=chat_namespace,
    )
    logger.warning(f"Error emitted for sid={sid}: {error_message}")
