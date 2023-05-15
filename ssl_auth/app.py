from flask import Flask
from flask import send_file
import config
app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello, world"


@app.route("/.well-known/pki-validation/CE3C2313F4FC06227B03EE646B38CF60.txt")
def send_auth_file():
    # return "FUCK"
    return send_file("CE3C2313F4FC06227B03EE646B38CF60.txt")


if __name__ == "__main__":
    app.run(
        host=config.HOST,
        port=config.PORT,
        ssl_context='adhoc'
    )