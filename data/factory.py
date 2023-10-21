from data import models
from data.database import Database, create_db
from data.file_manager import FileManager
import asyncio
import argparse
from configs import args_parse
from web_config.config import DB_URI

args = args_parse.args

# parser = argparse.ArgumentParser()
# parser.add_argument('--local', action='store_true', help='Run in local mode')
# parser.add_argument('--token', action='store', help='Bot token to run on')
# parser.add_argument('--port', action='store', help='Select the port to run on')
# parser.add_argument('--source', action='store', help='Database folder path')
# parser.add_argument('--logs', action='store', help='Logs folder path')
# args = parser.parse_args()

source = "source" if not args.source else args.source

asyncio.run(create_db(source))

file_manager = FileManager(source)
admins_db = Database("admins", DB_URI, models.Admin)
bots_db = Database("bots", DB_URI, models.Bot)
user_db = Database("users", DB_URI, models.User)
captchas_db = Database("captchas", DB_URI, models.Captcha)
greeting_db = Database("greetings", DB_URI, models.Greeting)
mails_db = Database("mails", DB_URI, models.Mail)
mails_queue_db = Database("mails_queue", DB_URI, models.MailsQueue)
purges_db = Database("purges", DB_URI, models.Purge)
msgs_db = Database("msgs", DB_URI, models.Msg)
multi_mails_db = Database("multi_mails", DB_URI, models.MultiMail)
