import os
from config import PORT, HOST
certfile_path = os.path.join(os.path.dirname(__file__), "certificate.crt")
keyfile_path = os.path.join(os.path.dirname(__file__), "private.key")
import uvicorn
from main import app
if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, ssl_certfile=certfile_path, ssl_keyfile=keyfile_path)