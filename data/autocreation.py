queries = [
    """
    CREATE TABLE  IF NOT EXISTS "admins" (
    "id"	INTEGER NOT NULL UNIQUE,
    "username"	TEXT,
    "first_name"	TEXT,
    "last_name"	TEXT,
    PRIMARY KEY("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "bots" (
        "id"	INTEGER NOT NULL UNIQUE,
        "token"	TEXT NOT NULL UNIQUE,
        "username"	TEXT NOT NULL,
        "admin"	INTEGER,
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
        "id"	INTEGER NOT NULL UNIQUE,
        "bot"	INTEGER NOT NULL,
        "active"	INTEGER NOT NULL,
        "text"	TEXT,
        "photo"	TEXT,
        "video"	TEXT,
        "gif"	TEXT,
        "buttons"	TEXT NOT NULL,
        "del_delay" INTEGER,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "greetings" (
        "id"	INTEGER NOT NULL UNIQUE,
        "bot"	INTEGER NOT NULL,
        "active"	INTEGER,
        "text"	TEXT,
        "photo"	TEXT,
        "video"	TEXT,
        "gif"	TEXT,
        "buttons"	TEXT,
        "send_delay"	INTEGER,
        "del_delay"	INTEGER,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "mails" (
        "id"	INTEGER NOT NULL UNIQUE,
        "bot"	INTEGER NOT NULL,
        "active"	INTEGER,
        "text"	TEXT,
        "photo"	TEXT,
        "video"	TEXT,
        "gif"	TEXT,
        "buttons"	TEXT,
        "send_dt"	TEXT,
        "del_dt"	TEXT,
        "status"	INTEGER NOT NULL,
        "sent_num"	INTEGER,
        "blocked_num"	INTEGER,
        "error_num"	INTEGER,
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "purges" (
        "id"	INTEGER NOT NULL UNIQUE,
        "bot"	INTEGER NOT NULL,
        "active"	INTEGER NOT NULL,
        "sched_dt"	INTEGER,
        "status"	INTEGER NOT NULL,
        "deleted_msgs_num"	INTEGER,
        "cleared_chats_num"	INTEGER,
        "error_num"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("bot") REFERENCES "bots"("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "users" (
        "id"	INTEGER NOT NULL,
        "bot"	INTEGER NOT NULL,
        "username"	TEXT,
        "first_name"	TEXT,
        "last_name"	TEXT,
        "status"	INTEGER NOT NULL,
        "join_dt"	TEXT NOT NULL,
        PRIMARY KEY("id","bot"),
        FOREIGN KEY("bot") REFERENCES "bots"("id")
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "msgs" (
        "id"	INTEGER NOT NULL UNIQUE,
        "user"	INTEGER NOT NULL,
        "bot"	INTEGER NOT NULL,
        "del_dt"	INTEGER,
        PRIMARY KEY("id", "bot"),
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        FOREIGN KEY("user") REFERENCES "users"("id")
    );
    """,
    """
        CREATE TABLE IF NOT EXISTS "admin_mails" (
        "id"	INTEGER NOT NULL UNIQUE,
        "active"	INTEGER,
        "text"	TEXT,
        "photo"	TEXT,
        "video"	TEXT,
        "gif"	TEXT,
        "buttons"	TEXT,
        "send_dt"	TEXT,
        "status"	INTEGER NOT NULL,
        "sent_num"	INTEGER,
        "blocked_num"	INTEGER,
        "error_num"	INTEGER,
        "sender" INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    """,
    """
        CREATE TABLE IF NOT EXISTS "mails_queue" (
        "id"	INTEGER NOT NULL UNIQUE,
        "bot"	INTEGER NOT NULL,
        "user"	INTEGER NOT NULL,
        "mail_id" INTEGER NOT NULL,
        "admin_status"	INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("bot") REFERENCES "bots"("id"),
        FOREIGN KEY("user") REFERENCES "users"("id")
    );
    """
]
