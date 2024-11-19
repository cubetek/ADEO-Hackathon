import os
import tempfile
import shutil

def save_temp_file(file):
    """Save an uploaded file to a temporary file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(file.file.read())
        return temp.name

def delete_temp_file(file_path):
    """Delete a temporary file."""
    if os.path.exists(file_path):
        os.remove(file_path)

def create_temp_dir():
    """Create a temporary directory."""
    return tempfile.mkdtemp()

def delete_temp_dir(dir_path):
    """Delete a temporary directory."""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
