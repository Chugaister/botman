import os
from config import PORT, HOST
certfile_path = os.path.join(os.path.dirname(__file__), "certificate.crt")
keyfile_path = os.path.join(os.path.dirname(__file__), "private.key")
ca_bundle_path = os.path.join(os.path.dirname(__file__), "ca_bundle.crt")
import uvicorn
from main import app
if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, ssl_certfile=certfile_path, ssl_keyfile=keyfile_path, ssl_ca_certs=ca_bundle_path)