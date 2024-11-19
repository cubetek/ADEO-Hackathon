from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_pdf_file():
    with open("test_files/sample.pdf", "rb") as pdf_file:
        response = client.post("/uploadfile/", files={"file": pdf_file})
        assert response.status_code == 200
        assert "extracted_text" in response.json()
