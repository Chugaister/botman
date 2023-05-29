import os
import uvicorn

from web_config.config import PORT, HOST, PUBLIC_IP
from app import app

certfile_path = os.path.join(os.path.dirname(__file__), "web_config", PUBLIC_IP, "certificate.crt")
keyfile_path = os.path.join(os.path.dirname(__file__), "web_config", PUBLIC_IP, "private.key")
ca_bundle_path = os.path.join(os.path.dirname(__file__), "web_config", PUBLIC_IP, "ca_bundle.crt")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        ssl_certfile=certfile_path,
        ssl_keyfile=keyfile_path,
        ssl_ca_certs=ca_bundle_path
    )