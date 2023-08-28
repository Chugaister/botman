from data import models
from data.database import Database, get_db, create_db
from data.file_manager import FileManager
import asyncio
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--local', action='store_true', help='Run in local mode')
parser.add_argument('--token', action='store', help='Bot token to run on')
parser.add_argument('--port', action='store', help='Select the port to run on')
parser.add_argument('--source', action='store', help='Database folder path')
parser.add_argument('--logs', action='store', help='Logs folder path')
args = parser.parse_args()

source = "source" if not args.source else args.source

create_db(source)
db_conn = asyncio.run(get_db(source))

file_manager = FileManager(source)
admins_db = Database("admins", db_conn, models.Admin)
bots_db = Database("bots", db_conn, models.Bot)
user_db = Database("users", db_conn, models.User)
captchas_db = Database("captchas", db_conn, models.Captcha)
greeting_db = Database("greetings", db_conn, models.Greeting)
mails_db = Database("mails", db_conn, models.Mail)
mails_queue_db = Database("mails_queue", db_conn, models.MailsQueue)
purges_db = Database("purges", db_conn, models.Purge)
msgs_db = Database("msgs", db_conn, models.Msg)
multi_mails_db = Database("multi_mails", db_conn, models.MultiMail)
