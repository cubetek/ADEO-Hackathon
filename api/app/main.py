from fastapi import FastAPI
from app.core.config import settings
from app.core.logger import logger
from app.sockets import sio
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from socketio import ASGIApp
from fastapi.staticfiles import StaticFiles
import app.sockets.chat_socket
from app.routers import file_upload

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A FastAPI application for file uploads and text extraction.",
    version="1.0.0",
    debug=settings.DEBUG,
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]),
    ]
)

# Include routers
app.include_router(file_upload.router, prefix="/api/v1", tags=["File Upload"])
sio_app = ASGIApp(sio)
# app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/", sio_app)

# Application startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastAPI application...")
    # Perform any startup tasks here (e.g., connecting to databases)

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastAPI application...")
    # Perform any cleanup tasks here (e.g., closing database connections)

# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint to check service health.
    """
    return {"message": f"Welcome to {settings.APP_NAME}!"}
