from data import models
from data.database import Database, get_db, create_db
from data.file_manager import FileManager
import asyncio


async def main():
    global file_manager, admins_db, bots_db, user_db, captchas_db, greeting_db, mails_db, purges_db, msgs_db
    db_conn = await get_db(source)

    file_manager = FileManager(source)
    admins_db = Database("admins", db_conn, models.Admin)
    bots_db = Database("bots", db_conn, models.Bot)
    user_db = Database("users", db_conn, models.User)
    captchas_db = Database("captchas", db_conn, models.Captcha)
    greeting_db = Database("greetings", db_conn, models.Greeting)
    mails_db = Database("mails", db_conn, models.Mail)
    purges_db = Database("purges", db_conn, models.Purge)
    msgs_db = Database("msgs", db_conn, models.Msg)

source = "source"
create_db(source)
asyncio.run(main())
