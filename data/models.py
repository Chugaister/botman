from datetime import datetime


DT_FORMAT = "%H:%M %d.%m.%Y"


def deserialize_buttons(text: str) -> list[dict]:
    buttons = []
    if text is None:
        return buttons
    for row in text.split("\n"):
        caption, link = row.split(" - ")
        buttons.append({
            "caption": caption,
            "link": link
        })
    return buttons


def serialize_buttons(buttons: list[dict]) -> str:
    if buttons == []:
        return None
    text = "\n".join([f"{button['caption']} - {button['link']}" for button in buttons])
    return text


class Admin:

    columns = (
        "id",
        "username",
        "first_name",
        "last_name"
    )

    def __init__(self, _id: int, username: str, first_name: str, last_name: str):
        self.id = _id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def get_tuple(self):
        return self.id, self.username, self.first_name, self.last_name


class Bot:

    columns = (
        "id",
        "token",
        "username",
        "admin",
        "premium",
    )

    def __init__(self, _id: int, token: str, username: str, admin: int, premium: int):
        self.id = _id
        self.token = token
        self.username = username
        self.admin = admin
        self.premium = premium

    def get_tuple(self):
        return self.id, self.token, self.username, self.admin, self.premium


class User:

    columns = (
        "id",
        "username",
        "first_name",
        "last_name",
        "status",
        "join_dt"
    )

    def __init__(self, _id: int, username: str, first_name: str, last_name: str, status: bool, join_dt: str):
        self.id = _id,
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.join_dt = datetime.strptime(join_dt, DT_FORMAT)

    def get_tuple(self):
        return self.id, self.username, self.first_name, self.last_name, self.status, self.join_dt.strftime(DT_FORMAT)


class Captcha:

    columns = (
        "bot",
        "text",
        "photo",
        "video",
        "gif",
        "buttons"
    )

    def __init__(self, _id: int, bot: int, text: str, photo: str, video: str, gif: str, buttons: list[str]):
        self.id = _id
        self.bot = bot
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = buttons

    def get_tuple(self):
        return self.bot, self.text, self.photo, self.video, self.gif, self.buttons


class Greeting:

    columns = (
        "bot",
        "active",
        "text",
        "photo",
        "video",
        "gif",
        "buttons",
        "send_delay",
        "del_delay"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool = False,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
            buttons: str = None,
            send_delay: int = None,
            del_delay: int = None
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = deserialize_buttons(buttons)
        self.send_delay = send_delay
        self.del_delay = del_delay

    def get_tuple(self):
        return (
            self.bot,
            self.active,
            self.text,
            self.photo,
            self.video,
            self.gif,
            serialize_buttons(self.buttons),
            self.send_delay,
            self.del_delay
        )


class Mail:

    columns = (
            "bot",
            "active",
            "text",
            "photo",
            "video",
            "gif",
            "buttons",
            "sched_dt",
            "del_delay",
            "status",
            "sent_num",
            "blocked_num",
            "error_num"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool,
            text: str,
            photo: str,
            video: str,
            gif: str,
            buttons: list[dict[str, str]],
            sched_dt: str,
            del_delay: str,
            status: bool,
            sent_num: int,
            blocked_num: int,
            error_num: int
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = buttons
        self.sched_dt = datetime.strptime(sched_dt, DT_FORMAT)
        self.del_delay = del_delay
        self.status = status
        self.sent_num = sent_num
        self.blocked_num = blocked_num
        self.error_num = error_num

    def get_tuple(self):
        return (
            self.bot,
            self.text,
            self.photo,
            self.video,
            self.gif,
            self.buttons,
            self.sched_dt.strftime(DT_FORMAT),
            self.del_delay,
            self.status,
            self.sent_num,
            self.blocked_num,
            self.error_num
        )


class Purge:

    columns = (
            "bot",
            "active",
            "sched_dt",
            "status",
            "deleted_msgs_num",
            "cleared_chats_num",
            "error_num"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool,
            sched_dt: str,
            status: bool,
            deleted_msgs_num: int,
            cleared_chats_num: int,
            error_num: int
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.sched_dt = datetime.strptime(sched_dt, DT_FORMAT)
        self.status = status
        self.deleted_msgs_num = deleted_msgs_num
        self.cleared_chats_num = cleared_chats_num
        self.error_num = error_num

    def get_tuple(self):
        return (
            self.bot,
            self.active,
            self.sched_dt.strftime(DT_FORMAT),
            self.status,
            self.deleted_msgs_num,
            self.cleared_chats_num,
            self.error_num,
        )


class Msg:

    columns = (
        "id",
        "user",
        "bot",
        "del_dt",
    )

    def __init__(self, _id: int, user: int, bot: int, del_dt: str):
        self.id = _id
        self.user = user
        self.bot = bot
        self.del_dt = datetime.strptime(del_dt, DT_FORMAT)

    def get_tuple(self):
        return self.id, self.user, self.bot, self.del_dt


