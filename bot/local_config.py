from pyngrok import ngrok, conf
from pyngrok import conf
PORT = 8080
HOST = '0.0.0.0'

conf.get_default().ngrok_version = "v3"

ngrok_tunnel = ngrok.connect(PORT)
PUBLIC_IP = ngrok_tunnel.public_url[len('https://'):]
# print(PUBLIC_IP)

WEBHOOK_HOST = PUBLIC_IP
print(PUBLIC_IP)