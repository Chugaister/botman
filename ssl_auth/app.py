from flask import Flask, send_file
import config


app = Flask(__name__)


@app.route('/')
def handle_webhook(token):
    return "OK"


@app.route(f"/.well-known/pki-validation/{config.auth_file_name}")
def send_auth_file():
    return send_file(config.auth_file_name)


if __name__ == "__main__":
    app.run(
        host=config.HOST,
        port=config.PORT,
        ssl_context='adhoc'
    )