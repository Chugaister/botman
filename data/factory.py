from data import models
from data.database import Database, get_db, create_db
from data.file_manager import FileManager

source = "source"
create_db(source)
db_conn = get_db(source)

file_manager = FileManager(source)
admins_db = Database("admins", db_conn, models.Admin)
bots_db = Database("bots", db_conn, models.Bot)
user_db = Database("users", db_conn, models.User)
captchas_db = Database("captchas", db_conn, models.Captcha)
greeting_db = Database("greetings", db_conn, models.Greeting)
mails_db = Database("mails", db_conn, models.Mail)
purges_db = Database("purges", db_conn, models.Purge)
msgs_db = Database("msgs", db_conn, models.Msg)