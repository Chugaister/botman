from gevent.pywsgi import WSGIServer
from app import app
import config

http_server = WSGIServer((config.HOST, config.PORT), app)
http_server.serve_forever()
