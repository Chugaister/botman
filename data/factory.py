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
args = parser.parse_args()
async def main(source):
    create_db(source)
    db_conn = await get_db(source)

    file_manager = FileManager(source)
    admins_db = Database("admins", db_conn, models.Admin)
    bots_db = Database("bots", db_conn, models.Bot)
    user_db = Database("users", db_conn, models.User)
    captchas_db = Database("captchas", db_conn, models.Captcha)
    greeting_db = Database("greetings", db_conn, models.Greeting)
    mails_db = Database("mails", db_conn, models.Mail)
    admin_mails_db = Database("admin_mails", db_conn, models.AdminMail)
    purges_db = Database("purges", db_conn, models.Purge)
    msgs_db = Database("msgs", db_conn, models.Msg)
    return file_manager, admins_db, bots_db, user_db, captchas_db, greeting_db, mails_db, admin_mails_db, purges_db, msgs_db
source = "source" if not args.source else args.source
print(args.source)
create_db(source)
file_manager, admins_db, bots_db, user_db, captchas_db, greeting_db, mails_db, admin_mails_db, purges_db, msgs_db = asyncio.run(main(source))
