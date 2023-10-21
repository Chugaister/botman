queries = [
    """
    CREATE TABLE  IF NOT EXISTS "admins" (
    "id"	BIGINT NOT NULL UNIQUE,
    "username"	TEXT,
    "first_name"	TEXT,
    "last_name"	TEXT,
    PRIMARY KEY("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "bots" (
        "id"	BIGINT NOT NULL UNIQUE,
        "token"	TEXT NOT NULL UNIQUE,
        "username"	TEXT NOT NULL,
        "admin"	BIGINT,
        "status"	INTEGER NOT NULL,
        "premium"	INTEGER NOT NULL,
        "settings"	INTEGER NOT NULL,
        "action" TEXT,
        FOREIGN KEY("admin") REFERENCES "admins"("id"),
        PRIMARY KEY("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "captchas" (
        "id"	SERIAL NOT NULL UNIQUE,
        "bot"	BIGINT NOT NULL,
        "active"    BOOL NOT NULL,
        "text"	TEXT,
        "photo"	TEXT,
        "video"	TEXT,
        "gif"	TEXT,
        "buttons"	TEXT NOT NULL,
        "del_delay" INTEGER,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        PRIMARY KEY("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "greetings" (
        "id"	SERIAL NOT NULL UNIQUE,
        "bot"	BIGINT NOT NULL,
        "active"	BOOL,
        "text"	TEXT,
        "photo"	TEXT,
        "video"	TEXT,
        "gif"	TEXT,
        "buttons"	TEXT,
        "send_delay"	INTEGER,
        "del_delay"	INTEGER,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        PRIMARY KEY("id")
    );
    """,
"""
    CREATE TABLE IF NOT EXISTS "multi_mails" (
        "id"	SERIAL NOT NULL UNIQUE,
        "sender" BIGINT NOT NULL,
        "bots"	TEXT NOT NULL,
        "active"	BOOL,
        "text"	TEXT,
        "photo"	TEXT,
        "video"	TEXT,
        "gif"	TEXT,
        "buttons"	TEXT,
        "send_dt"	TEXT,
        "del_dt"	TEXT,
        "status"	BOOL NOT NULL,
        "sent_num"	INTEGER,
        "blocked_num"	INTEGER,
        "error_num"	INTEGER,
        PRIMARY KEY("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "mails" (
        "id"	SERIAL NOT NULL UNIQUE,
        "sender" BIGINT NOT NULL,
        "bot"	BIGINT NOT NULL,
        "active"	BOOL,
        "text"	TEXT,
        "photo"	TEXT,
        "video"	TEXT,
        "gif"	TEXT,
        "buttons"	TEXT,
        "send_dt"	TEXT,
        "del_dt"	TEXT,
        "status"	BOOL NOT NULL,
        "sent_num"	INTEGER,
        "blocked_num"	INTEGER,
        "error_num"	INTEGER,
        "file_id" TEXT,
        "multi_mail" INTEGER,
        "start_time" TEXT,
        "end_time" TEXT,
        "duration" TEXT,
        FOREIGN KEY("multi_mail") REFERENCES "multi_mails"("id"),
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        PRIMARY KEY("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "purges" (
        "id"	SERIAL NOT NULL UNIQUE,
        "sender" BIGINT NOT NULL,
        "bot"	BIGINT NOT NULL,
        "active"	BOOL NOT NULL,
        "sched_dt"	TEXT,
        "status"	BOOL NOT NULL,
        "deleted_msgs_num"	INTEGER,
        "cleared_chats_num"	INTEGER,
        "error_num"	INTEGER,
        "mail_id" INTEGER,
        "start_time" TEXT,
        "end_time" TEXT,
        "duration" TEXT,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        FOREIGN KEY("mail_id") REFERENCES "mails"("id"),
        PRIMARY KEY("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "users" (
        "id"	BIGINT NOT NULL,
        "bot"	BIGINT NOT NULL,
        "username"	TEXT,
        "first_name"	TEXT,
        "last_name"	TEXT,
        "status"	BOOL NOT NULL,
        "join_dt"	TEXT NOT NULL,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        PRIMARY KEY("id", "bot")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "msgs" (
        "id"	BIGINT NOT NULL,
        "user"	BIGINT NOT NULL,
        "bot"	BIGINT NOT NULL,
        "mail_id"	INTEGER,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        FOREIGN KEY("mail_id") REFERENCES "mails"("id"),
        PRIMARY KEY("id")
    );
    """,
    """
        CREATE TABLE IF NOT EXISTS "mails_queue" (
        "id"	SERIAL NOT NULL UNIQUE,
        "bot"	BIGINT NOT NULL,
        "user"	BIGINT NOT NULL,
        "mail_id" INTEGER NOT NULL,
        "admin_status"	BOOL NOT NULL,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        PRIMARY KEY("id")
    );
    """
]
