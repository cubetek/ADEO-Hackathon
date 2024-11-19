# README.md

# FastAPI File Upload and Text Extraction Service

This repository contains a **FastAPI** application designed for uploading files, extracting text, and managing real-time communication via **Socket.IO**.

## Features

- **File Upload and Text Extraction**:
  - Extract text from PDF, DOCX, and TXT files.
- **Real-time Communication**:
  - Built-in **Socket.IO** integration for live updates.
- **API First**:
  - RESTful API endpoints for client interaction.
- **Configurable Middleware**:
  - CORS enabled for cross-origin requests.
- **Production-Ready**:
  - Leverages **Gunicorn** and **Uvicorn** for robust deployment.

---

## Requirements

### Python Version

- Python 3.10+

### Dependencies

The project relies on the following libraries:

```plaintext
fastapi==0.100.0           # FastAPI framework
uvicorn[standard]==0.23.2  # ASGI server
PyPDF2==3.0.1              # For extracting text from PDF files
python-docx==0.8.11        # For extracting text from DOCX files
chardet==5.2.0             # For detecting text encoding in TXT files
pydantic==2.9              # For data validation and settings management
pytest==7.4.0              # For testing
pytest-asyncio==0.21.0     # For testing async code
python-dotenv==1.0.0       # For .env file management
gunicorn==23.0.0           # Production-grade WSGI server
python-multipart           # For handling file uploads
python-socketio[asyncio]==5.4.0
```

Install all dependencies with:

```bash
pip install -r requirements.txt
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo-name/fastapi-text-extraction
cd fastapi-text-extraction
```

### 2. Configure Environment Variables

Create a `.env` file at the root of the project:

```plaintext
APP_NAME=FastAPI File Upload Service
DEBUG=True
```

### 3. Start the Server

Run the development server:

```bash
uvicorn main:app --reload
```

Or start with Gunicorn for production:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### 4. Access the Application

- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Project Structure

```plaintext
.
├── app/
│   ├── routers/
│   │   └── file_upload.py         # Router for file upload endpoints
│   ├── core/
│   │   ├── config.py              # Application settings
│   │   └── logger.py              # Logging configuration
│   └── __init__.py
├── main.py                        # Entry point for the FastAPI app
├── requirements.txt               # List of Python dependencies
└── .env                           # Environment variables
```

---

## API Endpoints

### File Uploads

| Method | Endpoint        | Description                      |
|--------|-----------------|----------------------------------|
| `POST` | `/api/v1/upload` | Upload and process a file.       |

### Real-time Socket.IO

| Event Name       | Description                               |
|------------------|-------------------------------------------|
| `connect`        | Handles new client connections.          |
| `message`        | Processes client messages.               |
| `getConversations` | Fetches predefined conversation data.   |
| `sendMessage`    | Broadcasts messages to relevant clients. |

---

## Testing

Run tests using **pytest**:

```bash
pytest
```

---

## Deployment

### Using Docker

1. Build the Docker image:

```bash
docker build -t fastapi-text-extraction .
```

2. Run the container:

```bash
docker run -d -p 8000:8000 fastapi-text-extraction
```

---

## Contributors

- **Your Name** - [GitHub Profile](https://github.com/your-profile)

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.



to install and config ollama docker you need run run this commend


CPU
```
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

and for model  next run 

```
docker exec -it ollama ollama run llama3.1:8b
```

