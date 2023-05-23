from gevent.pywsgi import WSGIServer
from api import app
import config
import ssl
import os

certfile_path = os.path.join(os.path.dirname(__file__), "certificate.crt")
keyfile_path = os.path.join(os.path.dirname(__file__), "private.key")

http_server = WSGIServer(
    (config.HOST, config.PORT),
    app,
    certfile=certfile_path,
    keyfile=keyfile_path,
    ssl_version=ssl.PROTOCOL_TLS_SERVER,
    cert_reqs=ssl.CERT_NONE
)
http_server.serve_forever()
