import socketio
from app.core.logger import logger


sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[],
    logger=False,
    # engineio_logger=True,
    # ping_timeout=60,
    # ping_interval=25,
    # max_http_buffer_size=1000000
)


@sio.event(namespace='/chat-socket')
async def connect(sid, environ):
    # send welcome message to the client
    await sio.emit('response', {'data': 'Welcome!'}, to=sid)
    print(f"Client connected: {sid}")

@sio.event(namespace='/chat-socket')
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event(namespace='/chat-socket')
async def message(sid, data):
    print(f"Message from {sid}: {data}")
    # Emit response back to the client
    await sio.emit('response', {'data': f'Server received: {data}'}, to=sid, namespace='/chat-socket')

