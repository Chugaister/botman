from gevent.pywsgi import WSGIServer
from app import app
import config
import ssl


http_server = WSGIServer(
    (config.HOST, config.PORT),
    app,
    certfile="certificate.crt",
    keyfile="private.key",
    ssl_version=ssl.PROTOCOL_TLS,
    cert_reqs=ssl.CERT_NONE
)
http_server.serve_forever()
